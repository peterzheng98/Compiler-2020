package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	_ "github.com/go-sql-driver/mysql"
	"net/http"
)

func getUserList(w http.ResponseWriter, r *http.Request){
	// Fetch the user list in the database
	db, err := sql.Open("mysql", "username:password@tcp(127.0.0.1:3306)/compiler")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		// send empty message
		return
	}
	if db == nil{
		fmt.Printf("runtime Error: Database open failed.(db is nil)")
		// send empty message
		_, _ = fmt.Fprint(w, "Internal Error")
		return
	}
	defer db.Close()
	// Execute the query
	result, err := db.Query("SELECT uuid, repo FROM userDatabase")
	if err != nil{
		fmt.Printf("runtime Error: %s", err.Error())
		_, _ = fmt.Fprint(w, "{Internal Error}")
		return
	}
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
	fmt.Fprint(w, sendMap)
	fmt.Printf("send: %s", sendMap)
}

func getTask(w http.ResponseWriter, r *http.Request) {

}

func addUser(w http.ResponseWriter, r *http.Request){

}

func reqJudge(w http.ResponseWriter, r *http.Request){
	// Structure: {'uuid', 'repo', 'stage':[1,2,3]}
}

func addData(w http.ResponseWriter, r *http.Request){
	// add the data into database
}

func removeData(w http.ResponseWriter, r *http.Request){
	// remove the data in the database
}


func main() {
	http.HandleFunc("/fetchRepo", getUserList) // Get
	http.HandleFunc("/fetchTask", getTask) // Get
	http.HandleFunc("/addUser", addUser) // Post
	http.HandleFunc("/requestJudge", reqJudge) // Post
	http.HandleFunc("/addData", addData) // Post
	http.HandleFunc("/removeData", removeData) // Post
	fmt.Print("Hello World")
}
