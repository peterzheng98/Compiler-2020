/*
Test Package: Sema_Local_Preview
Test Target: Basic
Author: 16' Hongyu Yan
Time: 2019-11-11
Verdict: Success
Origin Package: Semantic Pretest
*/
int yhy(int yhy){
	return yhy;
}

int main() {
	A c;
	return yhy(c.b.a.b.a.v[10]);
}
class A {
	int [] v = new int[3];
	B b;
};
class B {
	A a;
};
