package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /fetchRepoWeb
func getUserListWeb(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("[*] Request from: %s\n", r.Host)
	// Fetch the user list in the database
	result, err := executionQuery("SELECT stu_id, stu_repo, stu_name, stu_judge_status FROM userDatabase")
	if result == nil {
		fmt.Printf("runtime Error: execution with return empty cursor.")
		return
	}
	var userDatSent map[string][]string
	userDatSent = make(map[string][]string)
	var index = 0
	defer result.Close()
	for result.Next() {
		var userUuid string
		var userRepo string
		var userName string
		var userJudge string
		err = result.Scan(&userUuid, &userRepo, &userName, &userJudge)
		dataSent := [] string{userUuid, userName, userRepo, userJudge}
		if err != nil {
			fmt.Printf("runtime warning:%s when scanning %s", err.Error(), userUuid)
			_, _ = fmt.Fprint(w, "Internal Error")
		}
		userDatSent[fmt.Sprint(index)] = dataSent
		index = index + 1
	}
	_ = json.NewEncoder(w).Encode(sendFormatWeb{
		Code:    200,
		Message: userDatSent,
	})
}

