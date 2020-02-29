package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// /addDataSemantic test ok!
func addDataSemantic(w http.ResponseWriter, r *http.Request) {
	// add the data into database
	var record dataSemanticFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in creating data. ErrMsg: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	fmt.Printf("[*] data:%s\n", record)
	uid := n.Next()
	SQLcommand := fmt.Sprintf("INSERT INTO Dataset_semantic(sema_uid, sema_sourceCode, sema_assertion, sema_timeLimit, sema_memoryLimit, sema_instLimit, sema_testcase) "+
		"VALUES ('%s', '%s', %t, %.2f, %d, %d, '%s')", uid, record.SourceCode, record.Assertion, record.TimeLimit, record.MemoryLimit, record.InstLimit, record.Testcase)
	_, err = executionExec(SQLcommand)
	if err != nil {
		fmt.Printf("runtime error: %s\n", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", uid)
}

