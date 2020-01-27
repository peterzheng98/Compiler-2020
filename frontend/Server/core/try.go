package main

import (
	"encoding/json"
	"fmt"
	"github.com/nats-io/nuid"
	"net/http"
	"strings"
)

type mysubstr struct {
	Uuid string `json:"uuid"`
	Rtt2 int    `json:"rtt_2"`
}

type mystr struct {
	Uuid string     `json:"uuid"`
	Rttl []mysubstr `json:"rttl"`
}

func hello(w http.ResponseWriter, req *http.Request) {
	var res []mysubstr
	res = append(res, mysubstr{
		Uuid: "!34232",
		Rtt2: 123,
	})
	enc := json.NewEncoder(w)
	err := enc.Encode(mystr{
		Uuid: "adsg",
		Rttl: nil,
	})
	if err != nil{
		fmt.Printf(err.Error())
	}
	//fmt.Fprintf(w, "{\"hello\":123}")
}

func headers(w http.ResponseWriter, req *http.Request) {
	var arr mysubstr
	err := json.NewDecoder(req.Body).Decode(&arr)
	if err != nil{
		fmt.Printf("111")
	}
	for name, headers := range req.Header {
		for _, h := range headers {
			_, err := fmt.Fprintf(w, "%v: %v\n", name, h)
			if err != nil{
				fmt.Printf("Error: %s", err.Error())
			}
			fmt.Printf("%v: %v\n", name, h)
		}
	}

}
var nd = nuid.New()
func main() {
	var rtt []int
	rtt = append(rtt, 1, 2)
	//fmt.Print(rtt)
	rtt = append(rtt[1:])
	//fmt.Print(rtt)
	rtt = append(rtt[1:])
	//fmt.Print(rtt)
	//需要先导入strings包
	s1 := "字符串"
	fmt.Printf("\n[%s]\n", nd.Next())
	fmt.Printf("\n[%s]\n", nuid.New().Next())
	fmt.Printf("\n[%s]\n", nuid.New().Next())

	s2 := "拼接"
	//定义一个字符串数组包含上述的字符串
	var str []string = []string{s1, s2}
	//调用Join函数
	s3 := strings.Join(str, " OR id=")
	fmt.Print(s3)
	rtt = append(rtt, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
	for k, v := range rtt{
		fmt.Printf("%d->%d %s\n", k, v, rtt)
		rtt = append(rtt[0:k], rtt[k+1:]...)

	}
	//http.HandleFunc("/hello", hello)
	//http.HandleFunc("/headers", headers)
	//
	//http.ListenAndServe(":8090", nil)
}