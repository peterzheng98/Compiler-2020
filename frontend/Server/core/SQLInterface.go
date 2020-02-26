package main

import (
	"database/sql"
	"fmt"
)

func executionQuery(cmd string) (*sql.Rows, error) {
	// Execute the query
	result, err := db.Query(cmd)
	if err != nil {
		fmt.Printf("runtime Error: %s\n", err.Error())
		return nil, err
	}
	if result == nil {
		fmt.Printf("runtime Error: execution with return empty cursor.\n")
		return nil, fmt.Errorf("execution with return empty cursor")
	}
	return result, err
}

func executionExec(cmd string) (sql.Result, error) {
	result, err := db.Exec(cmd)
	if err != nil {
		fmt.Printf("runtime Error: %s\n", err.Error())
		return nil, err
	}
	return result, err
}

