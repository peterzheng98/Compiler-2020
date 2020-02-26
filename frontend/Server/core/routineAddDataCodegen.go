package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /addDataCodegen test ok!
func addDataCodegen(w http.ResponseWriter, r *http.Request) {
	// add the data into database
	var record dataCodegenFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in creating data. ErrMsg: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	fmt.Printf("[*] data:%s\n", record)
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
	if err != nil {
		fmt.Printf("runtime error: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", uid)
}
