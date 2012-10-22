% Find Children

descendants(X,Y) :- parent(X,Y).
descendants(X,Y) :- parent(X,Z),descendants(Z,Y).

parent_state(Y,Z) :- parent(X,Y),state(X,Z).

ancestor(Y,X,P) :- parent(X,Y),state(X,'UP'),ports(Y,P).
ancestor(Y,X,P) :- parent(X,Y),(state(X,'DOWN');state(X,'UNREACHABLE')),parent(Z,X),ancestor(X,Z,P).

paradoxes(X,Y) :- parent(X,Y),state(Y,'UP'),\+ state(X,'UP'),\+ (parent(C,Y),state(C,'UP')),\+ (parent(Y,Z),state(Z,'UP')).

blocked(X,Y) :- \+ state(Y,'UP'),descendants(X,Y),state(X,'DOWN').

