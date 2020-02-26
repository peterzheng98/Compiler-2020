package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /fetchRepo test ok!
func getUserList(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("[*] Request from: %s\n", r.Host)
	// Fetch the user list in the database
	result, err := executionQuery("SELECT stu_uuid, stu_repo FROM userDatabase")
	if result == nil {
		fmt.Printf("runtime Error: execution with return empty cursor.")
		return
	}
	var userDatSent map[string]string
	userDatSent = make(map[string]string)
	defer result.Close()
	for result.Next() {
		var userUuid string
		var userRepo string
		err = result.Scan(&userUuid, &userRepo)
		if err != nil {
			fmt.Printf("runtime warning:%s when scanning %s", err.Error(), userUuid)
			_, _ = fmt.Fprint(w, "Internal Error")
		}
		userDatSent[userUuid] = userRepo
	}
	_ = json.NewEncoder(w).Encode(sendFormat{
		Code:    200,
		Message: userDatSent,
	})
	sendMap, _ := json.Marshal(userDatSent)
	fmt.Printf("\t[√] send: %s\n", sendMap)
}