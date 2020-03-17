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
	if _, ok := compilePool[dispatchedResult.Ident]; ok {
		// Insert result into the database
		sqlCmd := fmt.Sprintf("INSERT INTO judgeResult(judge_p_githash, judge_p_judgeid, judge_p_repo, judge_p_useruuid, judge_p_gitMessage, judge_p_verdict, judge_p_build_result, judge_p_build_message) VALUES ('%s', '%s', '%s', '%s', '%s', %d, '%s', '%s')",
			dispatchedResult.GitHash, dispatchedResult.RecordID, dispatchedResult.Repo, dispatchedResult.UUID, dispatchedResult.GitCommit, verdictBuild, dispatchedResult.Verdict, dispatchedResult.BuildMessage)
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

			var poolElement JudgePoolElement
			poolElement.Repo = dispatchedResult.Repo
			poolElement.Uuid = dispatchedResult.UUID
			poolElement.Build = true
			poolElement.RecordID = dispatchedResult.RecordID

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
			poolElement.RunningSet = make(map[string]bool)
			for result.Next() {
				var id string
				err = result.Scan(&id)
				if err != nil {
					logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 1)
				}
				poolElement.Pending = append(poolElement.Pending, id)

			}
			semanticPool = append(semanticPool, poolElement)
			// update user status
			updateCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=4 WHERE stu_uuid='%s' AND stu_repo='%s'", dispatchedResult.UUID, dispatchedResult.Repo)
			_, sqlErr := executionExec(updateCmd)
			if sqlErr != nil {
				logger(fmt.Sprintf("SQL Runtime error: %s", sqlErr.Error()), 1)
				_ = json.NewEncoder(w).Encode(simpleSendFormat{
					Code:    400,
					Message: fmt.Sprint(sqlErr.Error()),
				})
				return
			}

			_ = json.NewEncoder(w).Encode(simpleSendFormat{
				Code:    200,
				Message: fmt.Sprint("Accept the result"),
			})
			delete(compilePool, dispatchedResult.Ident)
			logger(fmt.Sprintf("=========================================="), 1)
			logger(fmt.Sprintf("[*] Request Added, current semantic pool: length=%d", len(semanticPool)), 1)
			for idx, d := range semanticPool {
				logger(fmt.Sprintf("Record[%d]: %s", idx, d), 0)
			}
			logger(fmt.Sprintf("=========================================="), 1)
		} else {
			// Build failed
			commandStr := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=3 WHERE (stu_uuid='%s' AND  judge_p_repo='%s')", dispatchedResult.UUID, dispatchedResult.Repo)
			_, err = executionExec(commandStr)
			if err != nil {
				logger(fmt.Sprintf("Runtime error[Semantic]: %s", err.Error()), 1)
			}
			_ = json.NewEncoder(w).Encode(simpleSendFormat{
				Code:    200,
				Message: fmt.Sprint("Accept the result"),
			})
			delete(compilePool, dispatchedResult.Ident)

		}
	} else {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    200,
			Message: fmt.Sprint("Recently built."),
		})
	}
}
