package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func fetchCompileTask(w http.ResponseWriter, r *http.Request) {
	// Structure: {'uuid', 'repo'}
	// add listen port
	var record requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		logger(fmt.Sprintf("Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}

	var poolElement JudgePoolElement
	poolElement.repo = record.Repo
	poolElement.uuid = record.Uuid
	poolElement.recordID = n.Next()
	poolElement.build = false

	compilePool = append(compilePool, poolElement)
	sqlCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=0 WHERE stu_uuid='%s' AND stu_repo='%s'", record.Uuid, record.Repo)
	_, err = executionExec(sqlCmd)
	if err != nil {
		logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    401,
			Message: fmt.Sprintf("SQL Runtime error: %s", err.Error()),
		})
		return
	}
	logger(fmt.Sprintf("=========================================="), 1)
	logger(fmt.Sprintf("[*] Request Added, current compile pool: length=%d", len(compilePool)), 1)
	for idx, d := range compilePool {
		logger(fmt.Sprintf("Record[%d]: %s", idx, d), 0)
	}
	logger(fmt.Sprintf("=========================================="), 1)
	_ = json.NewEncoder(w).Encode(simpleSendFormat{
		Code:    200,
		Message: fmt.Sprint("Judge in queue."),
	})
}
