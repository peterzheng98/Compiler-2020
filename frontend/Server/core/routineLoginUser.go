package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// @/loginUser
func loginUser(w http.ResponseWriter, r *http.Request) {
	var record userLoginFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in login user, host: %s, message: %s\n", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
	}
	SQLcmd := fmt.Sprintf("SELECT stu_uuid, stu_name, stu_password FROM userDatabase WHERE stu_id='%s'", record.StuID)
	result, sqlerr := executionQuery(SQLcmd)
	if sqlerr != nil {
		fmt.Printf("runtime error: not success in login user, host: %s, message: %s\n", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", sqlerr.Error())
	}
	defer result.Close()
	var verified = false
	var loginUserData = make(map[string]string)
	for result.Next() {
		var password string
		var username string
		var useruuid string
		err = result.Scan(&useruuid, &username, &password)
		if err != nil {
			continue
		}
		if password == record.StuPassword {
			verified = true
			loginUserData["name"] = username
			loginUserData["uuid"] = useruuid
			break
		}
	}
	if verified {
		_ = json.NewEncoder(w).Encode(sendFormat{
			Code:    200,
			Message: loginUserData,
		})
	} else {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: "Login failed!",
		})
	}

}
