import peewee as pw
from datetime import datetime
from config import DATABASE_NAME

db = pw.SqliteDatabase(DATABASE_NAME, pragmas={'journal_mode': 'wal'})


class BaseModel(pw.Model):
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    class Meta:
        database = db


class ForwardMessage(BaseModel):
    source_chat_id = pw.CharField(max_length=255)
    source_message_id = pw.IntegerField()
    is_active = pw.BooleanField(default=True)
    forward_count = pw.IntegerField(default=0)
    last_forward_date = pw.DateTimeField(null=True)

    class Meta:
        table_name = 'forward_messages'
        indexes = (
            (('source_chat_id', 'source_message_id'), True),
        )

    @classmethod
    def add_message(cls, chat_id, message_id):
        cls.deactivate_message(chat_id, message_id)

        obj, created = cls.get_or_create(
            source_chat_id=chat_id,
            source_message_id=message_id,
            defaults={
                'is_active': True,
                'forward_count': 0
            }
        )
        if not created:
            obj.is_active = True
            obj.save()

        return obj

    @classmethod
    def deactivate_message(cls, chat_id, message_id):
        old_active = cls.get_active_message()
        if not old_active:
            return
        if old_active.source_chat_id == chat_id and old_active.source_message_id == message_id:
            return False
        else:
            old_active.is_active = False
            old_active.save()
            return True

    @classmethod
    def get_active_message(cls):
        try:
            return cls.get(cls.is_active == True)
        except pw.DoesNotExist:
            return None

    def forward(self):
        self.forward_count += 1
        self.last_forward_date = datetime.now()
        self.save()


class GroupInfo(BaseModel):
    group_id = pw.CharField(primary_key=True, max_length=255, unique=True,)
    group_title = pw.CharField(max_length=500, null=True)
    group_username = pw.CharField(max_length=255, null=True)
    group_link = pw.CharField(max_length=500, null=True)
    is_banned = pw.BooleanField(default=False)
    forward_enabled = pw.BooleanField(default=True)
    last_forward_date = pw.DateTimeField(null=True)

    class Meta:
        table_name = 'group_infos'
        indexes = (
            (('group_id',), True),
        )

    @classmethod
    def add_group(cls, group_id, group_title=None, group_username=None, group_link=None):
        obj, created = cls.get_or_create(
            group_id=group_id,
            defaults={
                'group_title': group_title,
                'group_username': group_username,
                'group_link': group_link,
                'is_banned': False,
                'forward_enabled': True
            }
        )
        if not created:
            if group_title:
                obj.group_title = group_title
            if group_username:
                obj.group_username = group_username
            if group_link:
                obj.group_link = group_link
            obj.save()
        return obj

    @classmethod
    def get_group(cls, group_id):
        try:
            return cls.get(cls.group_id == group_id)
        except pw.DoesNotExist:
            return None

    @classmethod
    def set_ban(cls, group_id):
        try:
            obj = cls.get(cls.group_id == group_id)
            obj.is_banned = True
            obj.forward_enabled = False
            obj.save()
            return obj
        except pw.DoesNotExist:
            return None


class ForwardHistory(BaseModel):
    message = pw.ForeignKeyField(ForwardMessage, backref='forwards')
    group = pw.ForeignKeyField(GroupInfo, backref='forwards')
    forward_date = pw.DateTimeField(default=datetime.now)
    success = pw.BooleanField(default=True)
    error_message = pw.TextField(null=True)

    class Meta:
        table_name = 'forward_histories'
        indexes = (
            (('message', 'group', 'forward_date'), False),
        )

    @classmethod
    def create_history(cls, message_id, group_id, success=True, error=None):
        return cls.create(
            message=message_id,
            group=group_id,
            success=success,
            error_message=error
        )

    @classmethod
    def get_group_history(cls, group_id, limit=100):
        return (cls
                .select()
                .where(cls.group == group_id)
                .order_by(cls.forward_date.desc())
                .limit(limit))

    @classmethod
    def get_message_history(cls, message_id, limit=100):
        return (cls
                .select()
                .where(cls.message == message_id)
                .order_by(cls.forward_date.desc())
                .limit(limit))

    @classmethod
    def get_today_stats(cls):
        today = datetime.now().date()
        return (cls
                .select(cls.group, pw.fn.COUNT(cls.id).alias('count'))
                .where(pw.fn.date(cls.forward_date) == today)
                .group_by(cls.group))


class ForwardManager:
    @staticmethod
    def send_message_to_group(message_id, group_id):
        try:
            message = ForwardMessage.get_by_id(message_id)
            group = GroupInfo.get(GroupInfo.group_id == group_id)

            if group.is_banned:
                ForwardHistory.create_history(message_id, group_id, False, "گروه بن شده است")
                return False, "گروه بن شده است"

            if not group.forward_enabled:
                ForwardHistory.create_history(message_id, group_id, False, "ارسال به این گروه غیرفعال است")
                return False, "ارسال به این گروه غیرفعال است"

            success = True
            error = None

            if success:
                message.forward_count += 1
                message.last_forward_date = datetime.now()
                message.save()

                group.last_forward_date = datetime.now()
                group.save()

            ForwardHistory.create_history(message_id, group_id, success, error)
            return success, "ارسال موفق" if success else f"ارسال ناموفق: {error}"

        except Exception as e:
            ForwardHistory.create_history(message_id, group_id, False, str(e))
            return False, f"خطا: {str(e)}"


def init_database():
    tables = [ForwardMessage, GroupInfo, ForwardHistory]
    db.create_tables(tables, safe=True)
    return db


if __name__ == "__main__":
    init_database()
    print("Database tables created successfully")