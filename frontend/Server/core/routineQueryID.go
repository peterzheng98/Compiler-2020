package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func queryID(w http.ResponseWriter, r *http.Request) {
	var record userLoginFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in login user, host: %s, message: %s\n", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
	}
	SQLcmd := fmt.Sprintf("SELECT stu_id, stu_name, stu_password, stu_repo FROM userDatabase WHERE stu_uuid='%s'", record.StuID)
	result, sqlerr := executionQuery(SQLcmd)
	if sqlerr != nil {
		fmt.Printf("runtime error: not success in login user, host: %s, message: %s\n", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", sqlerr.Error())
	}
	defer result.Close()
	var loginUserData = make(map[string]string)
	for result.Next() {
		var password string
		var username string
		var useruid string
		var userRepo string
		err = result.Scan(&useruid, &username, &password, &userRepo)
		if err != nil {
			continue
		}
		loginUserData["uid"] = useruid
		loginUserData["username"] = username
		loginUserData["password"] = password
		loginUserData["userrepo"] = userRepo
	}
	_ = json.NewEncoder(w).Encode(sendFormat{
		Code:    200,
		Message: loginUserData,
	})
}

