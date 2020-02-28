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
	poolElement.repo = record.Repo
	poolElement.uuid = record.Uuid
	poolElement.recordID = n.Next()
	poolElement.build = false
	var timeUnix = time.Now().Unix()
	compilePool[fmt.Sprint(timeUnix)] = poolElement

	// request for all the record in database
	result, err := executionQuery("SELECT sema_uid FROM dataset_semantic")
	if err != nil {
		logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}
	if result == nil {
		logger(fmt.Sprintf("Runtime error: Cannot fetch dataset_semantic"), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    401,
			Message: fmt.Sprint("Database error: Semantic database is empty"),
		})
		return
	}
	defer result.Close()

	for result.Next() {
		var id string
		err = result.Scan(&id)
		if err != nil {
			logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 1)
		}
		poolElement.pending = append(poolElement.pending, id)
	}
	semanticPool = append(semanticPool, poolElement)
	sqlCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=1 WHERE stu_uuid='%s' AND stu_repo='%s'", record.Uuid, record.Repo)
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
	logger(fmt.Sprintf("[*] Request Added, current semantic pool: length=%d", len(semanticPool)), 1)
	for idx, d := range semanticPool {
		logger(fmt.Sprintf("Record[%d]: %s", idx, d), 0)
	}
	logger(fmt.Sprintf("=========================================="), 1)
	_ = json.NewEncoder(w).Encode(simpleSendFormat{
		Code:    200,
		Message: fmt.Sprint("Judge in queue."),
	})
}
