package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /addUser test ok!
func addUser(w http.ResponseWriter, r *http.Request) {
	// Debug stage
	// Structure: stu_id+repo+name+password+email -> return uuid
	var record userAddFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in add user, host: %s, message: %s\n", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	userRealNNID := fmt.Sprintf("u%s", record.StuId)

	cmd := fmt.Sprintf("INSERT INTO UserDatabase(stu_uuid, stu_id, stu_repo, stu_name, stu_password, stu_email) VALUES ('%s', '%s', '%s', '%s', '%s', '%s');", userRealNNID, record.StuId, record.StuRepo, record.StuName, record.StuPassword, record.StuEmail)
	fmt.Printf("\t[*] [addUser] Execute SQL Command:%s\n", cmd)
	_, err = executionExec(cmd)
	if err != nil {
		fmt.Printf("runtime error: not success in add user, host: %s, message: %s\n", r.Host, fmt.Sprintf("%s", err.Error()))
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", fmt.Sprintf("%s", err.Error()))
		return
	}
	_, _ = fmt.Fprintf(w, "{\"code\": 200, \"message\": \"Added user %s -> %s\"}", record.StuId, userRealNNID)
}
