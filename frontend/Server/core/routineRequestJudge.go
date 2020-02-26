package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func reqJudge(w http.ResponseWriter, r *http.Request) {
	// Structure: {'uuid', 'repo'}
	// add listen port
	var record requestJudgeFormat
	err := json.NewDecoder(r.Body).Decode(&record)
	if err != nil {
		fmt.Printf("runtime error: not success in creating record.\n")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	// request for all the record in database
	result, err := executionQuery("SELECT sema_uid FROM dataset_semantic")
	if err != nil {
		fmt.Printf("runtime Error: %s", err.Error())
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", err.Error())
		return
	}
	if result == nil {
		fmt.Printf("runtime Error: %s", "Result is empty")
		_, _ = fmt.Fprintf(w, "{\"code\":400, \"message\": \"%s\"}", "Result is empty")
		return
	}
	defer result.Close()
	var poolElement JudgePoolElement
	poolElement.repo = record.Repo
	poolElement.uuid = record.Uuid
	poolElement.recordID = n.Next()
	for result.Next() {
		var id string
		err = result.Scan(&id)
		if err != nil {
			fmt.Printf("runtime warning:%s when scanning the semantic database", err.Error())
		}
		poolElement.pending = append(poolElement.pending, id)
	}
	semanticPool = append(semanticPool, poolElement)
	fmt.Printf("After: pool: %s\n", semanticPool)
	_, err = fmt.Fprintf(w, "{\"%s\": %d, \"%s\": \"%s\"}", "code", 200, "message", "123")
}


