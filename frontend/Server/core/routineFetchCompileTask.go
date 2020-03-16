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
			sentMess["repo"] = target.Repo
			sentMess["recordID"] = target.RecordID
			sentMess["uuid"] = target.Uuid

			sqlCmd := fmt.Sprintf("UPDATE userDatabase SET stu_judge_status=1 WHERE stu_uuid='%s' AND stu_repo='%s'", target.Uuid, target.Repo)
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
			logger(fmt.Sprintf("Sent compiler work: Repo:%s, UUID:%s", target.Repo, target.Uuid), 1)
			return
		}
	} else {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    404,
			Message: "No work found.",
		})
	}
}
