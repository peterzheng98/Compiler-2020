package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)
// /getStatusBrief
func getJudgeResult(w http.ResponseWriter, r *http.Request) {
	var judgeResult requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&judgeResult)
	if err != nil {
		logger(fmt.Sprintf("Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}
	id := judgeResult.Uuid
	jid := judgeResult.Repo
	sqlCmd := fmt.Sprintf("SELECT judge_p_build_result, judge_p_build_message, judge_p_gitMessage FROM judgeResult WHERE id=%s AND judge_p_judgeid='%s'", id, jid)
	result, sqlerr := executionQuery(sqlCmd)
	if sqlerr != nil {
		logger(fmt.Sprintf("Runtime error: %s", sqlerr.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(sqlerr.Error()),
		})
		return
	}
	defer result.Close()
	var buildResult string
	var buildMessage string
	var gitMessage string
	for result.Next() {
		result.Scan(&buildResult, &buildMessage, &gitMessage)
		break
	}
	var sentMess = make(map[string]string)
	sentMess["buildResult"] = buildResult
	sentMess["buildMessage"] = buildMessage
	sentMess["gitMessage"] = gitMessage
	_ = json.NewEncoder(w).Encode(sendFormat{
		Code:    200,
		Message: sentMess,
	})
}

// /getStatusDetail
func getJudgeResultDetail(w http.ResponseWriter, r *http.Request) {
	var judgeResult requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&judgeResult)
	if err != nil {
		logger(fmt.Sprintf("Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}
	judgeId := judgeResult.Uuid
	sqlCmd := fmt.Sprintf("SELECT judge_d_type, judge_d_testcase, judge_d_result, judge_d_judgeTime, judge_d_subworkId FROM JudgeDetail WHERE judge_p_judgeid='%s'", judgeId)
	result, sqlerr := executionQuery(sqlCmd)
	if sqlerr != nil {
		logger(fmt.Sprintf("Runtime error: %s", sqlerr.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(sqlerr.Error()),
		})
		return
	}
	defer result.Close()
	var sentResult [][]string
	for result.Next(){
		var judgeType string
		var judgeCase string
		var judgeResult string
		var judgeTime string
		var judgeWorkID string
		fmt.Printf("\n\n[%s]\n\n", judgeResult)
		result.Scan(&judgeType, &judgeCase, &judgeResult, &judgeTime, &judgeWorkID)
		sendElem := []string{judgeType, judgeCase, judgeResult, judgeTime, judgeWorkID}
		sentResult = append(sentResult, sendElem)
	}
	_ = json.NewEncoder(w).Encode(sendFormatList{
		Code:    200,
		Message: sentResult,
	})
}
