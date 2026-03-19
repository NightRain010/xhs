-- NL2SQL 查询平台 - 建表脚本
-- 注意：此脚本由 Docker 容器首次启动时自动执行

SET NAMES utf8mb4;
USE nl2sql_platform;

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username` VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    `email` VARCHAR(128) NOT NULL UNIQUE COMMENT '邮箱',
    `password_hash` VARCHAR(256) NOT NULL COMMENT '密码哈希值',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否激活',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 查询历史表
CREATE TABLE IF NOT EXISTS `query_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    `user_id` INT NOT NULL COMMENT '关联用户',
    `nl_input` TEXT NOT NULL COMMENT '用户自然语言输入',
    `intent_type` VARCHAR(32) DEFAULT NULL COMMENT '识别到的意图类型',
    `generated_sql` TEXT DEFAULT NULL COMMENT 'AI 生成的 SQL 语句',
    `query_result` JSON DEFAULT NULL COMMENT '查询结果',
    `status` ENUM('pending', 'success', 'failed', 'rejected') NOT NULL DEFAULT 'pending' COMMENT '查询状态',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    `execution_ms` INT DEFAULT NULL COMMENT 'SQL 执行耗时（毫秒）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_user_id` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='查询历史表';

-- 表结构元数据缓存表
CREATE TABLE IF NOT EXISTS `schema_metadata` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '元数据ID',
    `table_name` VARCHAR(128) NOT NULL COMMENT '表名',
    `column_name` VARCHAR(128) NOT NULL COMMENT '字段名',
    `column_type` VARCHAR(64) NOT NULL COMMENT '字段类型',
    `is_primary` TINYINT(1) DEFAULT 0 COMMENT '是否为主键',
    `is_nullable` TINYINT(1) DEFAULT 1 COMMENT '是否允许 NULL',
    `comment` VARCHAR(512) DEFAULT NULL COMMENT '字段注释',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_table_name` (`table_name`),
    UNIQUE KEY `uq_table_column` (`table_name`, `column_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表结构元数据缓存';

-- 教师表（业务示例）
CREATE TABLE IF NOT EXISTS `teachers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '教师ID',
    `name` VARCHAR(64) NOT NULL COMMENT '姓名',
    `title` VARCHAR(32) DEFAULT NULL COMMENT '职称',
    `department` VARCHAR(64) NOT NULL COMMENT '所属院系',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师表';

-- 学生表（业务示例）
CREATE TABLE IF NOT EXISTS `students` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '学生ID',
    `name` VARCHAR(64) NOT NULL COMMENT '姓名',
    `gender` ENUM('男', '女') NOT NULL COMMENT '性别',
    `birth_date` DATE DEFAULT NULL COMMENT '出生日期',
    `grade` VARCHAR(32) NOT NULL COMMENT '年级',
    `class_name` VARCHAR(32) NOT NULL COMMENT '班级',
    `enrollment_date` DATE NOT NULL COMMENT '入学日期',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生表';

-- 课程表（业务示例）
CREATE TABLE IF NOT EXISTS `courses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '课程ID',
    `name` VARCHAR(128) NOT NULL COMMENT '课程名称',
    `code` VARCHAR(32) NOT NULL UNIQUE COMMENT '课程编号',
    `credit` FLOAT NOT NULL COMMENT '学分',
    `teacher_id` INT NOT NULL COMMENT '授课教师',
    `semester` VARCHAR(32) NOT NULL COMMENT '学期',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`teacher_id`) REFERENCES `teachers`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 成绩表（业务示例）
CREATE TABLE IF NOT EXISTS `scores` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '成绩ID',
    `student_id` INT NOT NULL COMMENT '学生',
    `course_id` INT NOT NULL COMMENT '课程',
    `score` FLOAT NOT NULL COMMENT '分数',
    `exam_type` ENUM('期中', '期末', '平时') NOT NULL COMMENT '考试类型',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_student_id` (`student_id`),
    INDEX `idx_course_id` (`course_id`),
    UNIQUE KEY `uq_student_course_exam` (`student_id`, `course_id`, `exam_type`),
    FOREIGN KEY (`student_id`) REFERENCES `students`(`id`),
    FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成绩表';
