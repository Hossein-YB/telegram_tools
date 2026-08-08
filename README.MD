
## for create mysql Database use this code
```SQL
CREATE DATABASE tel_tool;
CREATE USER 'u_tel_tool'@'%' IDENTIFIED WITH mysql_native_password BY "tel_tool@bot";
GRANT ALL ON tel_tool.* TO 'u_tel_tool'@'%'; 
flush privileges;
```