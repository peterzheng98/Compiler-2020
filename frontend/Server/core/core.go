package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	_ "github.com/go-sql-driver/mysql"
	"github.com/nats-io/nuid"
	_ "github.com/nats-io/nuid"
	"net/http"
	"runtime/trace"
	"strings"
)

var n = nuid.New()
var user_nuid = nuid.New()
type sendFormat struct {
	Code int `json:"code"`
	Message map[string]string `json:"message"`
}

type userAddFormat struct{
	StuId string `json:"stu_id"`
	StuRepo string `json:"stu_repo"`
	StuName string `json:"stu_name"`
	StuPassword string `json:"stu_password"`
	StuEmail string `json:"stu_email"`
}

type dataSemanticFormat struct {
	SourceCode  string  `json:"source_code"`
	Assertion   bool    `json:"assertion"`
	TimeLimit   float32 `json:"time_limit, omitempty"`
	InstLimit   int     `json:"inst_limit, omitempty"`
	MemoryLimit int     `json:"memory_limit, omitempty"`
}

type dataCodegenFormat struct {
	SourceCode  string  `json:"source_code"`
	Assertion   bool    `json:"assertion"`
	TimeLimit   float32  `json:"time_limit, omitempty"`
	InstLimit   int     `json:"inst_limit, omitempty"`
	MemoryLimit int     `json:"memory_limit, omitempty"`
	InputContext string `json:"input_context"`
	OutputContext string `json:"output_context"`
	OutputCode int `json:"output_code"`
	BasicType int `json:"basic_type"`
}


type subtaskSemanticFormat struct {
	Uuid            string  `json:"uuid"`
	Repo            string  `json:"repo"`
	TestCase        string  `json:"testCase"`
	Stage           int     `json:"stage"`
	Subworkid       string  `json:"subWorkId"`
	InputSourceCode string  `json:"inputSourceCode"`
	Assertion       string  `json:"assertion"`
	TimeLimit       float32 `json:"timeLimit"`
	MemoryLimit     int     `json:"memoryLimit"`
	TaskID			string	`json:"taskID"`
}

type subtaskCodegenFormat struct {
	Uuid            string  `json:"uuid"`
	Repo            string  `json:"repo"`
	TestCase        string  `json:"testCase"`
	Stage           int     `json:"stage"`
	Subworkid       string  `json:"subWorkId"`
	InputSourceCode string  `json:"inputSourceCode"`
	InputContent    string  `json:"inputContent"`
	OutputCode      int  `json:"outputCode"`
	OutputContent   string  `json:"outputContent"`
	TimeLimit       float32 `json:"timeLimit"`
	MemoryLimit     int     `json:"memoryLimit"`
	TaskID			string	`json:"taskID"`
}

type requestCodegenTaskFormat struct{
	Code   int                    `json:"code"`
	Target []subtaskCodegenFormat `json:"target"`
}


type requestSemanticTaskFormat struct{
	Code   int                     `json:"code"`
	Target []subtaskSemanticFormat `json:"target"`
}

type requestJudgeFormat struct{
	Uuid string `json:"uuid"`
	Repo string `json:"repo"`
}

type submitTaskElement struct{
	SubworkId   string   `json:"subWorkId"`
	JudgeResult []string `json:"JudgeResult"`
	Judger      string   `json:"Judger"`
	JudgeTime   string   `json:"JudgeTime"`
	TestCase    string   `json:"testCase"`
	Judgetype   int      `json:"judgetype"`
	Uuid	    string   `json:"uuid"`
	GitHash		string   `json:"git_hash"`
	TaskID		string	`json:"taskID"`
}

type JudgePoolElement struct{
	uuid string
	repo string
	githash string
	recordID string
	success []string
	fail []string
	pending []string
	running []string
	total int
}

var semanticPool []JudgePoolElement
var codegenPool []JudgePoolElement
var optimizePool []JudgePoolElement
var db, _ = sql.Open("mysql", "client:password1A@tcp(127.0.0.1:3306)/compiler")
var db2, _ = sql.Open("mysql", "client:password1A@tcp(127.0.0.1:3306)/compiler")

func executionQuery(cmd string)(*sql.Rows, error){
	// Execute the query
	result, err := db.Query(cmd)
	if err != nil{
		fmt.Printf("runtime Error: %s\n", err.Error())
		return nil, err
	}
	if result == nil{
		fmt.Printf("runtime Error: execution with return empty cursor.\n")
		return nil, fmt.Errorf("execution with return empty cursor")
	}
	return result, err
}

func executionExec(cmd string)(sql.Result, error){
	result, err := db.Exec(cmd)
	if err != nil{
		fmt.Printf("runtime Error: %s\n", err.Error())
		return nil, err
	}
	return result, err
}
// /fetchRepo test ok!
func getUserList(w http.ResponseWriter, r *http.Request){
	fmt.Printf("[*] Request from: %s\n", r.Host)
	// Fetch the user list in the database
	result, err := executionQuery("SELECT stu_uuid, stu_repo FROM userDatabase")
	if result == nil{
		fmt.Printf("runtime Error: execution with return empty cursor.")
		return
	}
	var userDatSent map[string]string
	userDatSent = make(map[string]string)
	defer result.Close()
	for result.Next(){
		var userUuid string
		var userRepo string
		err = result.Scan(&userUuid, &userRepo)
		if err != nil{
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
	//_, _ = fmt.Fprint(w, sendMap)
	fmt.Printf("\t[√] send: %s\n", sendMap)
}
// /addUser test ok!
func addUser(w http.ResponseWriter, r *http.Request){
	// Debug stage
	// Structure: stu_id+repo+name+password+email -> return uuid
	var record userAddFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil{
		fmt.Printf("runtime error: not success in add user, host: %s, message: %s", r.Host, r.Body)
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
	}
	userNNID := user_nuid.Next()
	userRealNNID := fmt.Sprint(record.StuId)[9:] + userNNID

	cmd := fmt.Sprintf("INSERT INTO UserDatabase(stu_uuid, stu_id, stu_repo, stu_name, stu_password, stu_email) VALUES ('%s', '%s', '%s', '%s', '%s', '%s');", userRealNNID, record.StuId, record.StuRepo, record.StuName, record.StuPassword, record.StuEmail)
	fmt.Printf("\t[*] [addUser] Execute SQL Command:%s\n", cmd)
	_, err = executionExec(cmd)
	if err != nil{
		fmt.Printf("runtime error: not success in add user, host: %s, message: %s\n", r.Host,  fmt.Sprintf("%s", err.Error()))
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", fmt.Sprintf("%s", err.Error()))
		return
	}
	_, _ = fmt.Fprintf(w, "{\"code\": 200, \"message\": \"Added user %s -> %s\"}", record.StuId, userRealNNID)
}
// /addDataSemantic test ok!
func addDataSemantic(w http.ResponseWriter, r *http.Request){
	// add the data into database
	var record dataSemanticFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil{
		fmt.Printf("runtime error: not success in creating data. ErrMsg: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	fmt.Printf("[*] data:%s\n",record)
	uid := n.Next()
	SQLcommand := fmt.Sprintf("INSERT INTO Dataset_semantic(sema_uid, sema_sourceCode, sema_assertion, sema_timeLimit, sema_memoryLimit, sema_instLimit) " +
		"VALUES ('%s', '%s', %t, %.2f, %d, %d)", uid, record.SourceCode, record.Assertion, record.TimeLimit, record.MemoryLimit, record.InstLimit)
	_, err = executionExec(SQLcommand)
	if err != nil{
		fmt.Printf("runtime error: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", uid)
}
// /addDataCodegen test ok!
func addDataCodegen(w http.ResponseWriter, r *http.Request){
	// add the data into database
	var record dataCodegenFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil{
		fmt.Printf("runtime error: not success in creating data. ErrMsg: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	fmt.Printf("[*] data:%s\n",record)
	uid := n.Next()
	var SQLcommand string
	if record.BasicType == 1 {
		SQLcommand = fmt.Sprintf("INSERT INTO Dataset_optimize(optim_uid, optim_sourceCode, optim_assertion, optim_timeLimit, optim_memoryLimit, optim_instLimit, optim_inputCtx, optim_outputCtx, optim_outputCode) "+
			"VALUES ('%s', '%s', %t, %.2f, %d, %d, '%s', '%s', %d)", uid, record.SourceCode, record.Assertion, record.TimeLimit, record.MemoryLimit, record.InstLimit, record.InputContext, record.OutputContext, record.OutputCode)
	} else {
		SQLcommand = fmt.Sprintf("INSERT INTO Dataset_codegen(cg_uid, cg_sourceCode, cg_assertion, cg_timeLimit, cg_memoryLimit, cg_instLimit, cg_inputCtx, cg_outputCtx, cg_outputCode) "+
			"VALUES ('%s', '%s', %t, %.2f, %d, %d, '%s', '%s', %d)", uid, record.SourceCode, record.Assertion, record.TimeLimit, record.MemoryLimit, record.InstLimit, record.InputContext, record.OutputContext, record.OutputCode)

	}
	_, err = executionExec(SQLcommand)
	if err != nil{
		fmt.Printf("runtime error: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", uid)
}

func addOptimize(uuid string, repo string){
	element := JudgePoolElement{
		uuid:    uuid,
		repo:    repo,
		success: make([]string, 0),
		fail:    make([]string, 0),
		pending: make([]string, 0),
		running: make([]string, 0),
		total:   0,
	}
	result, err := executionQuery("SELECT optim_uid FROM dataset_optimize")
	if result == nil{
		fmt.Printf("runtime error: result is null")
		return
	}
	defer result.Close()

	for result.Next(){
		var id string
		err = result.Scan(&id)
		if err != nil{
			fmt.Printf("runtime warning:%s when scanning the optimize database", err.Error())
		}
		element.pending = append(element.pending, id)
	}
	optimizePool = append(optimizePool, element)
}

func addCodegen(uuid string, repo string){
	element := JudgePoolElement{
		uuid:    uuid,
		repo:    repo,
		success: make([]string, 0),
		fail:    make([]string, 0),
		pending: make([]string, 0),
		running: make([]string, 0),
		total:   0,
	}
	result, err := executionQuery("SELECT cg_uid FROM dataset_codegen")
	if result == nil{
		fmt.Printf("runtime error: result is null")
		return
	}
	defer result.Close()

	for result.Next(){
		var id string
		err = result.Scan(&id)
		if err != nil{
			fmt.Printf("runtime warning:%s when scanning the codegen database", err.Error())
		}
		element.pending = append(element.pending, id)
	}
	codegenPool = append(codegenPool, element)
}
// /fetchTask
func getTask(w http.ResponseWriter, r *http.Request) {
	if len(semanticPool) != 0{
		poolElement := semanticPool[0]
		var runningList []string
		remainPend := len(poolElement.pending)
		var idx = 0
		for ;remainPend == 0 && idx < len(semanticPool); idx++{
			poolElement = semanticPool[idx]
			remainPend = len(poolElement.pending)
			if remainPend != 0{
				break
			}
		}
		if remainPend != 0 {
			if remainPend < 5 {
				semanticPool[idx].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(semanticPool[idx].running, semanticPool[idx].pending)
				semanticPool[idx].pending = append(semanticPool[idx].pending[remainPend:])
			} else {
				semanticPool[idx].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(semanticPool[idx].running, semanticPool[idx].pending[0:5])
				semanticPool[idx].pending = append(semanticPool[idx].pending[5:])
			}
			_ = copy(runningList, semanticPool[idx].running)
			cmd := "SELECT sema_uid, sema_sourceCode, sema_assertion, sema_timeLimit, sema_memoryLimit FROM dataset_semantic WHERE " +
				"sema_uid='" + strings.Join(runningList, "' OR sema_uid='") + "'"
			fmt.Printf("Execution Sentence:%s\n", cmd)
			result, err := executionQuery(cmd)
			if err != nil {
				fmt.Printf("Error %s\n", err.Error())
				return
			}
			var sentReq requestSemanticTaskFormat
			sentReq.Code = 2
			sentReq.Target = make([]subtaskSemanticFormat, 0, 5)
			for result.Next() {
				var id string
				var sourceCode string
				var assert string
				var timeLimit float32
				var memoryLimit int
				err = result.Scan(&id, &sourceCode, &assert, &timeLimit, &memoryLimit)
				if err != nil {
					fmt.Printf("runtime warning:%s when scanning the semantic database\n", err.Error())
				}
				sentReq.Target = append(sentReq.Target, subtaskSemanticFormat{
					Uuid:            poolElement.uuid,
					Repo:            poolElement.repo,
					TestCase:        id,
					Stage:           1,
					Subworkid:       id + "_" + n.Next(),
					InputSourceCode: sourceCode,
					Assertion:       assert,
					TimeLimit:       timeLimit,
					MemoryLimit:     memoryLimit,
					TaskID:			 poolElement.recordID,
				})
			}

			err = json.NewEncoder(w).Encode(sentReq)
			if err != nil {
				fmt.Printf("runtime error: %s\n", err.Error())
			}
			return
		}
	}
	if len(codegenPool) != 0{
		poolElement := codegenPool[0]
		var runningList []string
		remainPend := len(poolElement.pending)
		var idx = 0
		for ;remainPend == 0 && idx < len(codegenPool); idx++{
			poolElement = codegenPool[idx]
			remainPend = len(poolElement.pending)
			if remainPend != 0{
				break
			}
		}
		if remainPend != 0 {
			if remainPend < 5 {
				codegenPool[idx].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(codegenPool[idx].running, codegenPool[idx].pending)
				codegenPool[idx].pending = append(codegenPool[idx].pending[remainPend:])
			} else {
				codegenPool[idx].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(codegenPool[idx].running, codegenPool[idx].pending[0:5])
				codegenPool[idx].pending = append(codegenPool[idx].pending[5:])
			}
			_ = copy(runningList, codegenPool[idx].running)
			cmd := "SELECT cg_uid, cg_sourceCode, cg_assertion, cg_timeLimit, cg_memoryLimit, cg_inputCtx, cg_outputCtx, cg_outputCode FROM dataset_codegen WHERE " +
				"cg_uid='" + strings.Join(runningList, "' OR cg_uid='") + "'"
			fmt.Printf("Execution Sentence:%s\n", cmd)
			result, err := executionQuery(cmd)
			if err != nil {
				fmt.Printf("Error %s", err.Error())
				return
			}
			var sentReq requestCodegenTaskFormat
			sentReq.Code = 2
			sentReq.Target = make([]subtaskCodegenFormat, 0, 5)
			for result.Next() {
				var id string
				var sourceCode string
				var assert string
				var timeLimit float32
				var memoryLimit int
				var inputContext string
				var outputContext string
				var outputCode int
				err = result.Scan(&id, &sourceCode, &assert, &timeLimit, &memoryLimit, &inputContext, &outputContext, &outputCode)
				if err != nil {
					fmt.Printf("runtime warning:%s when scanning the codegen database", err.Error())
				}
				sentReq.Target = append(sentReq.Target,subtaskCodegenFormat{
					Uuid:            poolElement.uuid,
					Repo:            poolElement.repo,
					TestCase:        id,
					Stage:           2,
					Subworkid:       id + "_" + n.Next(),
					InputSourceCode: sourceCode,
					InputContent:    inputContext,
					OutputCode:      outputCode,
					OutputContent:   outputContext,
					TimeLimit:       timeLimit,
					MemoryLimit:     memoryLimit,
					TaskID:			 poolElement.recordID,
				})
			}

			err = json.NewEncoder(w).Encode(sentReq)
			if err != nil {
				fmt.Printf("runtime error: %s", err.Error())
			}
			return
		}
	}
	if len(optimizePool) != 0{
		poolElement := optimizePool[0]
		var runningList []string
		remainPend := len(poolElement.pending)
		var idx = 0
		for ;remainPend == 0 && idx < len(optimizePool); idx++{
			poolElement = optimizePool[idx]
			remainPend = len(poolElement.pending)
			if remainPend != 0{
				break
			}
		}
		if remainPend != 0 {
			if remainPend < 5 {
				optimizePool[idx].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(optimizePool[idx].running, optimizePool[idx].pending)
				optimizePool[idx].pending = append(optimizePool[idx].pending[remainPend:])
			} else {
				optimizePool[idx].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(optimizePool[idx].running, optimizePool[idx].pending[0:5])
				optimizePool[idx].pending = append(optimizePool[idx].pending[5:])
			}
			_ = copy(runningList, optimizePool[idx].running)
			cmd := "SELECT optim_uid, optim_sourceCode, optim_assertion, optim_timeLimit, optim_memoryLimit, optim_inputCtx, optim_outputCtx, optim_outputCode FROM dataset_optimize WHERE " +
				"optim_uid='" + strings.Join(runningList, "' OR optim_uid='") + "'"
			fmt.Printf("Execution Sentence:%s\n", cmd)
			result, err := executionQuery(cmd)
			if err != nil {
				fmt.Printf("Error %s", err.Error())
				return
			}
			var sentReq requestCodegenTaskFormat
			sentReq.Code = 2
			sentReq.Target = make([]subtaskCodegenFormat, 0, 5)
			for result.Next() {
				var id string
				var sourceCode string
				var assert string
				var timeLimit float32
				var memoryLimit int
				var inputContext string
				var outputContext string
				var outputCode int
				err = result.Scan(&id, &sourceCode, &assert, &timeLimit, &memoryLimit, &inputContext, &outputContext, &outputCode)
				if err != nil {
					fmt.Printf("runtime warning:%s when scanning the codegen database", err.Error())
				}
				sentReq.Target = append(sentReq.Target,subtaskCodegenFormat{
					Uuid:            poolElement.uuid,
					Repo:            poolElement.repo,
					TestCase:        id,
					Stage:           3,
					Subworkid:       id + "_" + n.Next(),
					InputSourceCode: sourceCode,
					InputContent:    inputContext,
					OutputCode:      outputCode,
					OutputContent:   outputContext,
					TimeLimit:       timeLimit,
					MemoryLimit:     memoryLimit,
					TaskID:			 poolElement.recordID,
				})
			}

			err = json.NewEncoder(w).Encode(sentReq)
			if err != nil {
				fmt.Printf("runtime error: %s", err.Error())
			}
			return
		}
	}
	err := json.NewEncoder(w).Encode(requestSemanticTaskFormat{
		Code:   1,
		Target: nil,
	})
	if err != nil{
		fmt.Printf("runtime error: %s", err.Error())
	}
	return
}


func reqJudge(w http.ResponseWriter, r *http.Request){
	// Structure: {'uuid', 'repo'}
	// add listen port
	var record requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil{
		fmt.Printf("runtime error: not success in creating record.\n")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	// request for all the record in database
	result, err := executionQuery("SELECT sema_uid FROM dataset_semantic")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	if result == nil{
		fmt.Printf("runtime Error: %s", "Result is empty")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", "Result is empty")
		return
	}
	defer result.Close()
	var poolElement JudgePoolElement
	poolElement.repo = record.Repo
	poolElement.uuid = record.Uuid
	poolElement.recordID = n.Next()
	for result.Next(){
		var id string
		err = result.Scan(&id)
		if err != nil{
			fmt.Printf("runtime warning:%s when scanning the semantic database", err.Error())
		}
		poolElement.pending = append(poolElement.pending, id)
	}
	semanticPool = append(semanticPool, poolElement)
	fmt.Printf("After: pool: %s\n", semanticPool)
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", "123")
}


func removeData(w http.ResponseWriter, r *http.Request){
	// remove the data in the database
}

func submitTask(w http.ResponseWriter, r *http.Request){
	// dispatch the judge result
	var array []submitTaskElement
	err := json.NewDecoder(r.Body).Decode(&array)
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		// send empty message
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Unable to decode data\"}")
		return
	}
	// match the list
	for _, v := range array{
		if v.Judgetype == 1{
			// search in semantic
			var flag bool = false
			for idx, semanticV := range semanticPool{
				if semanticV.uuid == v.Uuid{
					semanticPool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "1" {
						semanticPool[idx].success = append(semanticPool[idx].success, v.SubworkId)
					} else {
						semanticPool[idx].fail = append(semanticPool[idx].fail, v.SubworkId)
					}
					for idx2, entry := range semanticV.running{
						if entry == v.TestCase{
							semanticPool[idx].running = append(semanticPool[idx].running[0:idx2], semanticPool[idx].running[idx2+1:]...)
							flag = true
							break
						}
					}
					if flag{
						break
					}
				}
			}
		} else if v.Judgetype == 2{
			// search in codegen
			var flag bool = false
			for idx, semanticV := range codegenPool{
				if semanticV.uuid == v.Uuid{
					codegenPool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "1" {
						codegenPool[idx].success = append(codegenPool[idx].success, v.SubworkId)
					} else {
						codegenPool[idx].fail = append(codegenPool[idx].fail, v.SubworkId)
					}
					for idx2, entry := range semanticV.running{
						if entry == v.TestCase{
							codegenPool[idx].running = append(codegenPool[idx].running[0:idx2], codegenPool[idx].running[idx2+1:]...)
							flag = true
							break
						}
					}
					if flag{
						break
					}
				}
			}
		} else {
			// search in optimize
			var flag bool = false
			for idx, semanticV := range optimizePool{
				if semanticV.uuid == v.Uuid{
					optimizePool[idx].githash = v.GitHash
					if v.JudgeResult[0] == "1" {
						optimizePool[idx].success = append(optimizePool[idx].success, v.SubworkId)
					} else {
						optimizePool[idx].fail = append(optimizePool[idx].fail, v.SubworkId)
					}
					for idx2, entry := range semanticV.running{
						if entry == v.TestCase{
							optimizePool[idx].running = append(optimizePool[idx].running[0:idx2], optimizePool[idx].running[idx2+1:]...)
							flag = true
							break
						}
					}
					if flag{
						break
					}
				}
			}
		}
	}
	// check whether the user can go into the next stage
	var RemoveIdx [][]int = make([][]int, 3)
	var wrongIdx [][]int = make([][]int, 3)
	for idx, v := range semanticPool{
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0{
			RemoveIdx[0] = append(RemoveIdx[0], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0{
			wrongIdx[0] = append(wrongIdx[0], idx)
		}
	}
	for idx, v := range codegenPool{
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0{
			RemoveIdx[1] = append(RemoveIdx[1], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0{
			wrongIdx[1] = append(wrongIdx[1], idx)
		}
	}
	for idx, v := range optimizePool{
		if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) == 0{
			RemoveIdx[2] = append(RemoveIdx[2], idx)
		} else if len(v.running) == 0 && len(v.pending) == 0 && len(v.fail) != 0{
			wrongIdx[2] = append(wrongIdx[2], idx)
		}
	}
	// check whether it should be sent into next stage
	for k, v := range RemoveIdx{
		for _, v2 := range v{
			if k == 0{
				sliceElement := semanticPool[v2]
				addCodegen(sliceElement.uuid, sliceElement.repo)
				fmt.Printf("\t[*] Semantic Judge Finish: %s - %s Semantic accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := "INSERT JudgeResult(judge_p_judgeid, judge_p_useruuid, judge_p_githash, judge_p_repo, judge_p_verdict, judge_p_semantic) VALUES('"
				dataString := sliceElement.recordID + "', '" + sliceElement.uuid + "','" + sliceElement.githash + "','" + sliceElement.repo + "', 2, '1[" + strings.Join(sliceElement.success, "/") + "]')"
				commandStr += dataString
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask-semantic]: %s\n", err.Error())
				}
				semanticPool = append(semanticPool[0:v2], semanticPool[v2+1:]...)
			}
			if k == 1{
				sliceElement := codegenPool[v2]
				addOptimize(sliceElement.uuid, sliceElement.repo)
				fmt.Printf("\t[*] Codegen Judge Finish: %s - %s Semantic accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_codegen ='%s' WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "1[" + strings.Join(sliceElement.success, "/") + "]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask-codegen]: %s\n", err.Error())
				}
				codegenPool = append(codegenPool[0:v2], codegenPool[v2+1:]...)
			}
			if k == 2{
				sliceElement := optimizePool[v2]
				fmt.Printf("Judge Finish: %s - %s All accepted\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_optimize ='%s', judge_p_verdict=1 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "1[" + strings.Join(sliceElement.success, "/") + "]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask]: %s\n", err.Error())
				}
				optimizePool = append(optimizePool[0:v2], optimizePool[v2+1:]...)
			}
		}
	}
	// remove the data if failed test
	for k, v := range wrongIdx{
		for _, v2 := range v{
			if k == 0{
				sliceElement := semanticPool[v2]
				fmt.Printf("\t[*] Semantic Judge Finish: %s - %s Semantic failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := "INSERT JudgeResult(judge_p_judgeid, judge_p_useruuid, judge_p_githash, judge_p_repo, judge_p_verdict, judge_p_semantic) VALUES('"
				dataString := sliceElement.recordID + "', '" + sliceElement.uuid + "','" + sliceElement.githash + "','" + sliceElement.repo + "', 0, '0[" + strings.Join(sliceElement.success, "/") + "][" + strings.Join(sliceElement.fail, "/") + "'])"
				commandStr += dataString
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask]: %s\n", err.Error())
				}
				semanticPool = append(semanticPool[0:v2], semanticPool[v2+1:]...)
			}
			if k == 1{
				sliceElement := codegenPool[v2]
				fmt.Printf("\t[*] Codegen Judge Finish: %s - %s Codegen failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_codegen ='%s', judge_p_verdict=0 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "0[" + strings.Join(sliceElement.success, "/") + "][" + strings.Join(sliceElement.fail, "/") + "]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-codegen-failed] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask-codegen]: %s\n", err.Error())
				}
				codegenPool = append(codegenPool[0:v2], codegenPool[v2+1:]...)
			}
			if k == 2{
				sliceElement := optimizePool[v2]
				fmt.Printf("\t[*] Optimize Judge Finish: %s - %s Optimize failed\n", sliceElement.uuid, sliceElement.repo)
				commandStr := fmt.Sprintf("UPDATE JudgeResult SET judge_p_optimize ='%s', judge_p_verdict=0 WHERE (judge_p_useruuid='%s' AND judge_p_githash='%s' AND judge_p_repo='%s' AND judge_p_judgeid='%s')", "0[" + strings.Join(sliceElement.success, "/") + "][" + strings.Join(sliceElement.fail, "/") + "]", sliceElement.uuid, sliceElement.githash, sliceElement.repo, sliceElement.recordID)
				fmt.Printf("[submitTask-optimize-failed] SQL:%s\n", commandStr)
				_, err := executionExec(commandStr)
				if err != nil{
					fmt.Printf("runtime error[submitTask-optimize-2]: %s\n", err.Error())
				}
				optimizePool = append(optimizePool[0:v2], optimizePool[v2+1:]...)
			}
		}
	}
	// add the judge result into database
	var commandStr string
	for _, v := range array{
		commandStr = "INSERT INTO JudgeDetail(judge_d_useruuid, judge_d_githash, judge_d_judger, judge_d_judgeTime, judge_d_subworkId, judge_d_testcase, judge_d_result, judge_d_type) VALUES ('"
		dataString := v.Uuid + "','" + v.GitHash + "','" + v.Judger + "','" + v.JudgeTime + "','" + v.SubworkId + "','" + v.TestCase + "','" + strings.Join(v.JudgeResult, "/") + "'," + fmt.Sprintf("%d)", v.Judgetype)
		commandStr += dataString
		_, err := executionExec(commandStr)
		if err != nil{
			trace.Log(context.Background(), "submitTask-SQL", err.Error())
		}
	}
}

func main() {
	db, err := sql.Open("mysql", "client:password1A@tcp(127.0.0.1:3306)/compiler")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		return
	}
	if db == nil{
		fmt.Printf("runtime Error: Database open failed.(db is nil)")
		return
	}
	defer db.Close()
	db2, err2 := sql.Open("mysql", "client:password1A@tcp(127.0.0.1:3306)/compiler")
	if err2 != nil{
		fmt.Printf("runtime Error: %s", err2.Error())
		return
	}
	if db2 == nil{
		fmt.Printf("runtime Error: Database open failed.(db is nil)")
		return
	}
	defer db2.Close()
	http.HandleFunc("/fetchRepo", getUserList) // Get test ok!
	http.HandleFunc("/fetchTask", getTask) // Get
	http.HandleFunc("/addUser", addUser) // Post test ok!
	http.HandleFunc("/requestJudge", reqJudge) // Post
	http.HandleFunc("/addDataSemantic", addDataSemantic) // Post semantic data test ok!
	http.HandleFunc("/addDataCodegen", addDataCodegen)// Post
	http.HandleFunc("/removeData", removeData) // Post
	http.HandleFunc("/submitTask", submitTask)
	fmt.Print("Start to serve\n")
	http.ListenAndServe(":10430", nil)
}
