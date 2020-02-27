package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"runtime/trace"
	"strings"
)

func submitTask(w http.ResponseWriter, r *http.Request) {
	// dispatch the judge result
	var array []submitTaskElement
	err := json.NewDecoder(r.Body).Decode(&array)
	if err != nil {
		logger(fmt.Sprintf("Runtime error: %s", err.Error()), 1)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprint(err.Error()),
		})
		return
	}
	// match the list
	for _, v := range array {
		if v.Judgetype == 1 {
			// search in semantic
			for idx, semanticV := range semanticPool {
				if semanticV.uuid == v.Uuid {
					semanticPool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "0" {
						delete(semanticPool[idx].runningSet, v.TestCase)
						semanticPool[idx].success = append(semanticPool[idx].success, v.SubworkId)
						semanticPool[idx].build = true
					} else if v.JudgeResult[0] == "2"{
						semanticPool[idx].build = false
					} else{
						semanticPool[idx].fail = append(semanticPool[idx].fail, v.SubworkId)
						semanticPool[idx].build = true
						delete(semanticPool[idx].runningSet, v.TestCase)
					}
				}
			}
		} else if v.Judgetype == 2 {
			// search in codegen
			for idx, semanticV := range codegenPool {
				if semanticV.uuid == v.Uuid {
					codegenPool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "0" {
						codegenPool[idx].success = append(codegenPool[idx].success, v.SubworkId)
						delete(codegenPool[idx].runningSet, v.TestCase)
					} else {
						codegenPool[idx].fail = append(codegenPool[idx].fail, v.SubworkId)
						delete(codegenPool[idx].runningSet, v.TestCase)
					}
				}
			}
		} else {
			// search in optimize
			for idx, semanticV := range optimizePool {
				if semanticV.uuid == v.Uuid {
					optimizePool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "1" {
						optimizePool[idx].success = append(optimizePool[idx].success, v.SubworkId)
						delete(optimizePool[idx].runningSet, v.TestCase)
					} else {
						optimizePool[idx].fail = append(optimizePool[idx].fail, v.SubworkId)
					}
				}
			}
		}
	}
	// check whether the user can go into the next stage
	var RemoveIdx [][]int = make([][]int, 3)
	var wrongIdx [][]int = make([][]int, 3)
	for idx, v := range semanticPool {
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0 {
			RemoveIdx[0] = append(RemoveIdx[0], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0 {
			wrongIdx[0] = append(wrongIdx[0], idx)
		}
	}
	for idx, v := range codegenPool {
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0 {
			RemoveIdx[1] = append(RemoveIdx[1], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0 {
			wrongIdx[1] = append(wrongIdx[1], idx)
		}
	}
	for idx, v := range optimizePool {
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0 {
			RemoveIdx[2] = append(RemoveIdx[2], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0 {
			wrongIdx[2] = append(wrongIdx[2], idx)
		}
	}
	// check whether it should be sent into next stage
	for k, v := range RemoveIdx {
		for _, v2 := range v {
			if k == 0 {
				sliceElement := semanticPool[v2]
				addCodegen(sliceElement.uuid, sliceElement.repo)
				fmt.Printf("\t[*] Semantic Judge Finish: %s - %s Semantic accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := "INSERT JudgeResult(judge_p_judgeid, judge_p_useruuid, judge_p_githash, judge_p_repo, judge_p_verdict, judge_p_semantic) VALUES('"
				dataString := sliceElement.recordID + "', '" + sliceElement.uuid + "','" + sliceElement.githash + "','" + sliceElement.repo + "', 2, '1[" + strings.Join(sliceElement.success, "/") + "]')"
				commandStr += dataString
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask-semantic]: %s\n", err.Error())
				}
				semanticPool = append(semanticPool[0:v2], semanticPool[v2+1:]...)
			}
			if k == 1 {
				sliceElement := codegenPool[v2]
				addOptimize(sliceElement.uuid, sliceElement.repo)
				fmt.Printf("\t[*] Codegen Judge Finish: %s - %s Semantic accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_codegen ='%s' WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "1["+strings.Join(sliceElement.success, "/")+"]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask-codegen]: %s\n", err.Error())
				}
				codegenPool = append(codegenPool[0:v2], codegenPool[v2+1:]...)
			}
			if k == 2 {
				sliceElement := optimizePool[v2]
				fmt.Printf("Judge Finish: %s - %s All accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_optimize ='%s', judge_p_verdict=1 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "1["+strings.Join(sliceElement.success, "/")+"]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask]: %s\n", err.Error())
				}
				optimizePool = append(optimizePool[0:v2], optimizePool[v2+1:]...)
			}
		}
	}
	// remove the data if failed test
	for k, v := range wrongIdx {
		for _, v2 := range v {
			if k == 0 {
				sliceElement := semanticPool[v2]
				fmt.Printf("\t[*] Semantic Judge Finish: %s - %s Semantic failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := "INSERT JudgeResult(judge_p_judgeid, judge_p_useruuid, judge_p_githash, judge_p_repo, judge_p_verdict, judge_p_semantic) VALUES('"
				dataString := sliceElement.recordID + "', '" + sliceElement.uuid + "','" + sliceElement.githash + "','" + sliceElement.repo + "', 0, '0[" + strings.Join(sliceElement.success, "/") + "][" + strings.Join(sliceElement.fail, "/") + "'])"
				commandStr += dataString
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask]: %s\n", err.Error())
				}
				semanticPool = append(semanticPool[0:v2], semanticPool[v2+1:]...)
			}
			if k == 1 {
				sliceElement := codegenPool[v2]
				fmt.Printf("\t[*] Codegen Judge Finish: %s - %s Codegen failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_codegen ='%s', judge_p_verdict=0 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "0["+strings.Join(sliceElement.success, "/")+"]["+strings.Join(sliceElement.fail, "/")+"]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen-failed] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask-codegen]: %s\n", err.Error())
				}
				codegenPool = append(codegenPool[0:v2], codegenPool[v2+1:]...)
			}
			if k == 2 {
				sliceElement := optimizePool[v2]
				fmt.Printf("\t[*] Optimize Judge Finish: %s - %s Optimize failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_optimize ='%s', judge_p_verdict=0 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "0["+strings.Join(sliceElement.success, "/")+"]["+strings.Join(sliceElement.fail, "/")+"]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-optimize-failed] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil {
					fmt.Printf("runtime error[submitTask-optimize-2]: %s\n", err.Error())
				}
				optimizePool = append(optimizePool[0:v2], optimizePool[v2+1:]...)
			}
		}
	}
	// add the judge result into database
	var commandStr string
	for _, v := range array {
		commandStr = "INSERT INTO JudgeDetail(judge_d_useruuid, judge_d_githash, judge_d_judger, judge_d_judgeTime, judge_d_subworkId, judge_d_testcase, judge_d_result, judge_d_type) VALUES ('"
		dataString := v.Uuid + "','" + v.GitHash + "','" + v.Judger + "','" + v.JudgeTime + "','" + v.SubworkId + "','" + v.TestCase + "','" + strings.Join(v.JudgeResult, "/") + "'," + fmt.Sprintf("%d)", v.Judgetype)
		commandStr += dataString
		_, err := executionExec(commandStr)
		if err != nil {
			trace.Log(context.Background(), "submitTask-SQL", err.Error())
		}
	}
}
