package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

func reqJudge(w http.ResponseWriter, r *http.Request) {
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
	poolElement.Repo = record.Repo
	poolElement.Uuid = record.Uuid
	poolElement.RecordID = n.Next()
	poolElement.Build = false
	var timeUnix = time.Now().Unix()
	compilePool[fmt.Sprint(timeUnix)] = poolElement
	logger(fmt.Sprintf("=========================================="), 1)
	logger(fmt.Sprintf("[*] Request Added, current compiler pool: length=%d", len(compilePool)), 1)
	for idx, d := range compilePool {
		logger(fmt.Sprintf("Record[%s]: %s", idx, d), 0)
	}
	logger(fmt.Sprintf("=========================================="), 1)
	_ = json.NewEncoder(w).Encode(simpleSendFormat{
		Code:    200,
		Message: fmt.Sprint("Judge in queue."),
	})
}
