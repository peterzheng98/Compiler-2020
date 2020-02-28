package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// fetchStatus
func getJudgeStatus(w http.ResponseWriter, r *http.Request) {
	// remove the data in the database
	var array []int
	err := json.NewDecoder(r.Body).Decode(&array)
	if err != nil {
		fmt.Printf("runtime Error: %s", err.Error())
		// send empty message
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Unable to decode data\"}")
		return
	}
	var start = array[0]
	var length = array[1]
	sqlCmd := fmt.Sprintf("SELECT id, judge_p_useruuid, judge_p_githash, judge_p_verdict, judge_p_judgetime, judge_p_judgeid from judgeResult order by id desc limit %d,%d;", start, length)
	result, err := executionQuery(sqlCmd)
	if err != nil {
		fmt.Printf("runtime Error: %s", err.Error())
		// send empty message
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Unable to decode data\"}")
		return
	}
	defer result.Close()
	var resultSent = make(map[string][]string)
	var index = 0
	for result.Next(){
		var userUuid string
		var userGithash string
		var userVerdict string
		var userJudgetime string
		var userJudgeID string
		var id string
		err = result.Scan(&id, &userUuid, &userGithash, &userVerdict, &userJudgetime, &userJudgeID)
		dataSent := [] string{userUuid, userGithash, userVerdict, userJudgetime, id, userJudgeID}
		if err != nil{
			fmt.Printf("[*]Internal Error, %s", err.Error())
			continue
		}
		resultSent[fmt.Sprint(index)] = dataSent
		index = index + 1
	}
	_ = json.NewEncoder(w).Encode(sendFormatWeb{
		Code:    200,
		Message: resultSent,
	})
}
