package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	_ "github.com/go-sql-driver/mysql"
	"github.com/nats-io/nuid"
	_ "github.com/nats-io/nuid"
	"net/http"
	"strings"
)

var n = nuid.New()
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
}

type JudgePoolElement struct{
	uuid string
	repo string
	success []string
	fail []string
	pending []string
	running []string
	total int
}

var semanticPool []JudgePoolElement
var codegenPool []JudgePoolElement
var optimizePool []JudgePoolElement

func executionQuery(cmd string)(*sql.Rows, error){
	db, err := sql.Open("mysql", "username:password@tcp(127.0.0.1:3306)/compiler")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		return nil, err
	}
	if db == nil{
		fmt.Printf("runtime Error: Database open failed.(db is nil)")
		return nil, fmt.Errorf("database open failed")
	}
	defer db.Close()
	// Execute the query
	result, err := db.Query(cmd)
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		return nil, err
	}
	if result == nil{
		fmt.Printf("runtime Error: execution with return empty cursor.")
		return nil, fmt.Errorf("execution with return empty cursor")
	}
	return result, err
}

func getUserList(w http.ResponseWriter, r *http.Request){
	// Fetch the user list in the database
	result, err := executionQuery("SELECT uuid, repo FROM userDatabase")
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
	sendMap, _ := json.Marshal(userDatSent)
	_, _ = fmt.Fprint(w, sendMap)
	fmt.Printf("send: %s", sendMap)
}

func getTask(w http.ResponseWriter, r *http.Request) {
	if len(semanticPool) != 0{
		poolElement := semanticPool[0]
		var runningList []string
		remainPend := len(poolElement.pending)
		var idx = 0
		for ;remainPend != 0 && idx < len(semanticPool); idx++{
			poolElement = semanticPool[idx]
			remainPend = len(poolElement.pending)
		}
		if remainPend != 0 {
			if remainPend < 5 {
				semanticPool[0].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(semanticPool[0].running, semanticPool[0].pending)
			} else {
				semanticPool[0].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(semanticPool[0].running, semanticPool[0].pending[0:5])
				semanticPool[0].pending = append(semanticPool[0].pending[5:])
			}
			_ = copy(runningList, semanticPool[0].running)
			cmd := "SELECT uid, sourceCode, assert, timeLimit, memoryLimit FROM dataset_semantic WHERE uid=" + strings.Join(runningList, " OR uid=")
			fmt.Printf("Execution Sentence:%s", cmd)
			result, err := executionQuery(cmd)
			if err != nil {
				fmt.Printf("Error %s", err.Error())
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
					fmt.Printf("runtime warning:%s when scanning the semantic database", err.Error())
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
				})
			}

			err = json.NewEncoder(w).Encode(sentReq)
			if err != nil {
				fmt.Printf("runtime error: %s", err.Error())
			}
			return
		}
	}
	if len(codegenPool) != 0{
		poolElement := codegenPool[0]
		var runningList []string
		remainPend := len(poolElement.pending)
		var idx = 0
		for ;remainPend != 0 && idx < len(codegenPool); idx++{
			poolElement = codegenPool[idx]
			remainPend = len(poolElement.pending)
		}
		if remainPend != 0 {
			if remainPend < 5 {
				codegenPool[0].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(codegenPool[0].running, codegenPool[0].pending)
			} else {
				codegenPool[0].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(codegenPool[0].running, codegenPool[0].pending[0:5])
				codegenPool[0].pending = append(codegenPool[0].pending[5:])
			}
			_ = copy(runningList, codegenPool[0].running)
			cmd := "SELECT uid, sourceCode, assert, timeLimit, memoryLimit, inputContext, outputContext, outputCode FROM dataset_codegen WHERE uid=" + strings.Join(runningList, " OR uid=")
			fmt.Printf("Execution Sentence:%s", cmd)
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
		for ;remainPend != 0 && idx < len(optimizePool); idx++{
			poolElement = optimizePool[idx]
			remainPend = len(poolElement.pending)
		}
		if remainPend != 0 {
			if remainPend < 5 {
				optimizePool[0].running = make([]string, remainPend)
				runningList = make([]string, remainPend)
				_ = copy(optimizePool[0].running, optimizePool[0].pending)
			} else {
				optimizePool[0].running = make([]string, 5)
				runningList = make([]string, 5)
				_ = copy(optimizePool[0].running, optimizePool[0].pending[0:5])
				optimizePool[0].pending = append(optimizePool[0].pending[5:])
			}
			_ = copy(runningList, optimizePool[0].running)
			cmd := "SELECT uid, sourceCode, assert, timeLimit, memoryLimit, inputContext, outputContext, outputCode FROM dataset_optimize WHERE uid=" + strings.Join(runningList, " OR uid=")
			fmt.Printf("Execution Sentence:%s", cmd)
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
// TODO: Not finished
func addUser(w http.ResponseWriter, r *http.Request){
	// Debug stage
	// Structure: id+repo+name+password+email -> return uuid
	db, err := sql.Open("mysql", "username:password@tcp(127.0.0.1:3306)/compiler")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		// send empty message
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Internal Error\"}")
		return
	}
	if db == nil{
		fmt.Printf("runtime Error: Database open failed.(db is nil)")
		// send empty message
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Internal Error\"}")
		return
	}
	defer db.Close()
	// Execute the query
	result, err := db.Query("SELECT uuid, repo FROM userDatabase")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		_, _ = fmt.Fprint(w, "{\"code\": 400, \"message\": \"Internal Error\"}")
		return
	}
	if result == nil{
		fmt.Printf("runtime Error: execution with return empty cursor.")
		return
	}
	_, _ = fmt.Fprintf(w, "{\"code\": 200, \"message\": \"Added user %s -> %s\"}", "111", "111")
}

func reqJudge(w http.ResponseWriter, r *http.Request){
	// Structure: {'uuid', 'repo'}
	// add listen port
	var record requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil{
		fmt.Printf("runtime error: not success in creating record.")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": %s}", err.Error())
	}
	// request for all the record in database
	result, err := executionQuery("SELECT uid FROM database_semantic")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": %s}", err.Error())
	}
	if result == nil{
		fmt.Printf("runtime Error: %s", "Result is empty")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": %s}", "Result is empty")
		return
	}
	defer result.Close()
	var poolElement JudgePoolElement
	poolElement.repo = record.Repo
	poolElement.uuid = record.Uuid
	for result.Next(){
		var id string
		err = result.Scan(&id)
		if err != nil{
			fmt.Printf("runtime warning:%s when scanning the semantic database", err.Error())
		}
		poolElement.pending = append(poolElement.pending, id)
	}
	semanticPool = append(semanticPool, poolElement)

	_, err = fmt.Fprintf(w, "{%s: %d}", "\"code\"", 200)
}

func addData(w http.ResponseWriter, r *http.Request){
	// add the data into database
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
					if v.JudgeResult[0] == "1" {
						semanticPool[idx].success = append(semanticPool[idx].success, v.TestCase)
					} else {
						semanticPool[idx].fail = append(semanticPool[idx].fail, v.TestCase)
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
					if v.JudgeResult[0] == "1" {
						codegenPool[idx].success = append(codegenPool[idx].success, v.TestCase)
					} else {
						codegenPool[idx].fail = append(codegenPool[idx].fail, v.TestCase)
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
					if v.JudgeResult[0] == "1" {
						optimizePool[idx].success = append(optimizePool[idx].success, v.TestCase)
					} else {
						optimizePool[idx].fail = append(optimizePool[idx].fail, v.TestCase)
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
	// add the judge result into database




	
	// check whether it should be sent into next stage

}



func main() {
	http.HandleFunc("/fetchRepo", getUserList) // Get
	http.HandleFunc("/fetchTask", getTask) // Get
	http.HandleFunc("/addUser", addUser) // Post
	http.HandleFunc("/requestJudge", reqJudge) // Post
	http.HandleFunc("/addData", addData) // Post
	http.HandleFunc("/removeData", removeData) // Post
	http.HandleFunc("/submitTask", submitTask)
	fmt.Print("Start to serve")
	http.ListenAndServe(":10430", nil)
}
