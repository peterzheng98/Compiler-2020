package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

func checkFileIsExist(filename string) bool {
	var exist = true
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		exist = false
	}
	return exist
}

func logger(src string, option int) {
	filename := "database.go.log"
	_, exefilename, line, _ := runtime.Caller(2)
	exefilename = filepath.Base(exefilename)
	if option == 1{
		fmt.Printf("[%s:%d]: %s\n", exefilename, line, src)
	}
	var f *os.File
	timeStr := time.Now().Format("2006-01-02 15:04:05")
	outputData := fmt.Sprintf("[%s][%s:%d]:%s\n", timeStr, exefilename, line, src)
	if checkFileIsExist(filename) { //如果文件存在
		f, _ = os.OpenFile(filename, os.O_WRONLY|os.O_APPEND, 0666) //打开文件
	} else {
		f, _ = os.Create(filename) //创建文件
	}
	_, _ = io.WriteString(f, outputData) //写入文件(字符串)
}
