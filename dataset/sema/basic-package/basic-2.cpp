/*
Test Package: Sema_Local_Preview
Test Target: Basic
Author: 15' Bohui Fang
Time: 2019-10-20
Verdict: Success
Origin Package: Semantic Extended
*/
void AA() {}
class B {}
int main() {
	int A;
	B C = new B;
	AA();
	A = 10;
	int B;
}