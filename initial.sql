create database compiler;
use compiler;
create table UserDatabase(
	id int not null primary key auto_increment,
    stu_uuid varchar(80) not null,
    stu_id varchar(12) not null unique,
    stu_repo text not null,
    stu_name text not null,
    stu_password varchar(40) not null,
    stu_email text not null
);
create table JudgeResult(
	id int not null primary key auto_increment,
    judge_p_useruuid varchar(80) not null,
    judge_p_repo text not null,
    judge_p_githash varchar(40) not null,
    judge_p_verdict int not null default 0,
    judge_p_semantic text not null,
    judge_p_codegen text not null,
    judge_p_optimize text not null,
    judge_p_judgetime text not null
);

create table JudgeDetail(
	id int not null primary key auto_increment,
    judge_d_useruuid varchar(80) not null,
    judge_d_judger varchar(16) not null default "",
    judge_d_judgeTime varchar(20) not null,
    judge_d_subworkId text not null,
    judge_d_testcase varchar(16) not null,
    judge_d_result text not null,
    judge_d_type int not null default 0
);

create table Dataset_semantic(
	id int not null primary key auto_increment,
    sema_uid varchar(16) not null,
    sema_sourceCode text not null,
    sema_assertion bool not null default false,
    sema_timeLimit float not null default -1,
    sema_instLimit int not null default 100000,
    sema_memoryLimit int not null default 512
);

create table Dataset_codegen(
	id int not null primary key auto_increment,
    cg_uid varchar(16) not null,
    cg_sourceCode text not null,
    cg_inputCtx text not null,
    cg_outputCtx text not null,
    cg_outputCode int not null,
    cg_assertion bool not null default false,
    cg_timeLimit float not null default -1,
    cg_instLimit int not null default 100000,
    cg_memoryLimit int not null default 512
);
    
    
create table Dataset_optimize(
	id int not null primary key auto_increment,
    optim_uid varchar(16) not null,
    optim_sourceCode text not null,
    optim_inputCtx text not null,
    optim_outputCtx text not null,
    optim_outputCode int not null,
    optim_assertion bool not null default false,
    optim_timeLimit float not null default -1,
    optim_instLimit int not null default 100000,
    optim_memoryLimit int not null default 512
);
    