package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /fetchBuild
func fetchCompileTask(w http.ResponseWriter, r *http.Request) {
	if len(compilePool) != 0 {
		for timestamp, target := range compilePool {
			var sentMess = make(map[string]string)
			sentMess["ident"] = timestamp
			sentMess["repo"] = target.repo
			sentMess["recordID"] = target.recordID
			sentMess["uuid"] = target.uuid

			sqlCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=1 WHERE stu_uuid='%s' AND stu_repo='%s'", target.uuid, target.repo)
			_, err := executionExec(sqlCmd)
			if err != nil {
				logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 1)
				_ = json.NewEncoder(w).Encode(simpleSendFormat{
					Code:    401,
					Message: fmt.Sprintf("SQL Runtime error: %s", err.Error()),
				})
				return
			}

			_ = json.NewEncoder(w).Encode(sendFormat{
				Code:    200,
				Message: sentMess,
			})
			logger(fmt.Sprintf("Sent compiler work: Repo:%s, UUID:%s", target.repo, target.uuid), 1)
			return
		}
	} else {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    404,
			Message: "No work found.",
		})
	}
}
