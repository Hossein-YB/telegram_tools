# Telegram Tools

A simple and extensible Telegram account management core with a management bot, database models, Telegram client wrapper, session management and operation history.

## Main parts

```text
Management Bot
      |
      v
AccountManager
  |       |       |
  v       v       v
Telegram  DB    Error Logger
Client
```

### 1. Management Bot

The bot is the interface between an operator/admin and the Telegram accounts that belong to that operator.

The intended flows are:

- add an operator
- add/remove an account
- enable/disable an account
- connect/disconnect an account
- join one or many groups
- use one account or many accounts for forwarding
- forward a message or media group to the groups of an account
- view operation history
- allow the Sudo user to manage operators and inspect global history

### 2. AccountManager

There is one `services.account_manager.AccountManager` instance per operator.

It owns the runtime clients, pending login state and account-related Telegram operations. It is also the middle layer between the bot and the database/Telegram client.

It does not contain Telegram implementation details; those stay in `TelegramClient`.

### 3. Database

Peewee models own their own database operations. Other layers call methods such as `get_account()`, `insert_account()`, `update_account()` and `delete_account()` instead of repeating Peewee queries throughout the project.

### Error logging vs operation history

These are intentionally different:

- `utils/logger.py` writes only errors/exceptions to `logs/errors.log`.
- `TelegramOperationTBL` stores operation history in MySQL, including successful and failed Telegram operations.
- `AccountManager` is the middle layer that records the operation and re-raises the original exception so the bot can show the error to the operator.

## Database relationships

```text
UsersTBL
   |
   | 1:N
   v
AccountsTBL
   |
   | 1:N
   +------> AccountCategoryTBL
   |
   | N:M through AccountGroupTBL
   v
GroupsTBL

UsersTBL 1:N TelegramOperationTBL N:1 AccountsTBL
```

- One user/operator can own many accounts.
- One account can belong to many groups.
- One group can belong to many accounts.
- `AccountGroupTBL` stores the account/group relationship and its joined/left state.
- `TelegramOperationTBL` stores which actor performed an operation and on which account.
- Sudo actions can therefore be distinguished from actions performed by the account owner.

## Important model methods

### UsersTBL

- `insert_user()`
- `update_user()`
- `delete_user()`
- `get_user()`
- `get_users()`
- `get_sudo()`
- `change_status()`
- `check_is_admin()`
- `check_is_sudo()`

### AccountsTBL

- `insert_account()`
- `update_account()`
- `delete_account()`
- `get_account()`
- `get_by_phone()`
- `get_admin_accounts()`
- `update_login()`
- `set_status()`
- `mark_connected()`
- `mark_disconnected()`
- `touch()`
- `activate()`
- `deactivate()`

### GroupsTBL

- `insert_group()`
- `update_group()`
- `delete_group()`
- `get_group()`
- `get_groups()`
- `deactivate()`

### AccountCategoryTBL

Kept as a small extension point for future grouping/category features.

- `insert_category()`
- `update_category()`
- `delete_category()`
- `get_category()`
- `get_account_categories()`

### AccountGroupTBL

- `insert_group()`
- `update_relation()`
- `delete_relation()`
- `get_relation_by_id()`
- `get_relation()`
- `get_account_groups()`
- `get_category_groups()`
- `exists()`
- `mark_left()`

### TelegramOperationTBL

- `insert_operation()`
- `update_operation()`
- `delete_operation()`
- `get_operation()`
- `get_account_operations()`
- `get_actor_operations()`
- `get_operator_operations()`
- `get_operations()`
- `get_errors()`

`log()` is kept as a compatibility alias for `insert_operation()`.

## TelegramClient methods

`telegram_client/telegram_client.py` is the Telegram-specific layer.

- `login()`
- `send_code()`
- `sign_in()`
- `check_password()`
- `load_me()`
- `get_me_info()`
- `get_all_dialogs()`
- `get_dialogs()` — returns groups only
- `get_groups()`
- `get_chat()`
- `join_group()`
- `leave_group()`
- `is_member()`
- `forward_messages()`
- `disconnect_client()`

A single message and a media group can both be passed to `forward_messages()` by using an integer or a list of message IDs.

## AccountManager methods

The important public methods are:

- `start_login()`
- `verify_login()`
- `connect_account()`
- `disconnect_account()`
- `set_account_active()`
- `delete_account()`
- `get_client()`
- `get_me()`
- `get_chat()`
- `get_dialogs()`
- `get_groups()`
- `join_group()`
- `join_group_for_accounts()`
- `leave_group()`
- `send_message()`
- `forward_message()`
- `forward_messages()`
- `forward_to_account_groups()`
- `forward_to_accounts_groups()`
- `get_messages()`

All Telegram operations that need common handling pass through `_run()`. That keeps error/history handling in one place instead of duplicating it in every method.

## Session flow

```text
Operator
   |
   | phone + account name
   v
start_login()
   |
   +--> create session path
   +--> send Telegram code
   |
   v
verify_login()
   |
   +--> code
   +--> optional 2FA password
   |
   v
AccountsTBL.update_login()
   |
   v
client kept in AccountManager.clients
```

Session files are created through `utils.manage_files` and are not stored in the database as session contents.

## Setup

1. Create the MySQL database/user using the SQL in this file or your own credentials.
2. Copy `.env.example` to `.env` and fill in the values.
3. Install requirements.
4. Run `main.py`.

During the design stage there is intentionally no migration system. The database can be dropped/recreated while the schema is still changing.

## Compatibility

The correct bot class name is `ClientManager`. `ClientManger` remains as an alias so existing code using the old spelling does not break.
