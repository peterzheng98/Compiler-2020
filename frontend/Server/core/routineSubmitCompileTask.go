package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /submitBuild
func submitBuildTask(w http.ResponseWriter, r *http.Request) {
	var dispatchedResult submitBuiltTaskElement
	err := json.NewDecoder(r.Body).Decode(&dispatchedResult)
	if err != nil {
		logger(fmt.Sprintf("Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}
	var verdictBuild = 2
	if dispatchedResult.Verdict != "Success" {
		verdictBuild = 0
	}
	// Insert result into the database
	sqlCmd := fmt.Sprintf("INSERT INTO judgeResult(judge_p_githash, judge_p_judgeid, judge_p_repo, judge_p_useruuid, judge_p_gitMessage, judge_p_verdict) VALUES ('%s', '%s', '%s', '%s', '%s', %d)",
		dispatchedResult.GitHash, dispatchedResult.RecordID, dispatchedResult.Repo, dispatchedResult.UUID, dispatchedResult.GitCommit, verdictBuild)
	_, sqlErr := executionExec(sqlCmd)
	if sqlErr != nil {
		logger(fmt.Sprintf("SQL Runtime error: %s", sqlErr.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(sqlErr.Error()),
		})
		return
	}
	if dispatchedResult.Verdict == "Success" {
		delete(compilePool, dispatchedResult.Ident)
		var poolElement JudgePoolElement
		poolElement.repo = dispatchedResult.Repo
		poolElement.uuid = dispatchedResult.UUID
		poolElement.build = true
		poolElement.recordID = dispatchedResult.RecordID

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
		// update user status
		updateCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=2 WHERE stu_uuid='%s' AND stu_repo='%s'", dispatchedResult.UUID, dispatchedResult.Repo)
		_, sqlErr := executionExec(updateCmd)
		if sqlErr != nil {
			logger(fmt.Sprintf("SQL Runtime error: %s", sqlErr.Error()), 1)
			_ = json.NewEncoder(w).Encode(simpleSendFormat{
				Code:    400,
				Message: fmt.Sprint(sqlErr.Error()),
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
			Message: fmt.Sprint("Accept the result"),
		})
	} else {
		// Build failed
		delete(compilePool, dispatchedResult.Ident)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    200,
			Message: fmt.Sprint("Accept the result"),
		})
	}
}