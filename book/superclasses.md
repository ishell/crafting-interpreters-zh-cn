# 超类

<!--
> You can choose your friends but you sho' can't choose your family, an' they're
> still kin to you no matter whether you acknowledge &rsquo;em or not, and it
> makes you look right silly when you don't.
>
> <cite>Harper Lee, <em>To Kill a Mockingbird</em></cite>
-->
> 朋友可以挑，可你没法挑家人；不管认不认，他们仍是你的亲人——不认，只会显得你傻。
>
> <cite>哈珀·李，<em>《杀死一只知更鸟》</em></cite>

<!--
This is the very last chapter where we add new functionality to our VM. We've
packed almost the entire Lox language in there already. All that remains is
inheriting methods and calling superclass methods. We have [another
chapter][optimization] after this one, but it introduces no new behavior. It
<span name="faster">only</span> makes existing stuff faster. Make it to the end
of this one, and you'll have a complete Lox implementation.
-->
这是我们给虚拟机加新功能的最后一章。差不多整门 Lox 语言都已塞进里头了。剩下的只有：继承方法，以及调用超类方法。这之后还有[另一章][optimization]，但并不引入新行为——它<span name="faster">仅仅</span>让已有的东西更快。读完本章，你就有一份完整的 Lox 实现。

<aside name="faster">

<!--
That "only" should not imply that making stuff faster isn't important! After
all, the whole purpose of our entire second virtual machine is better
performance over jlox. You could argue that *all* of the past fifteen chapters
are "optimization".
-->
那句“仅仅”可别暗示加快速度不重要！毕竟，整台第二虚拟机的全部目的，就是比 jlox 更好的性能。你甚至可以说，过去十五章*全都是*“优化”。

</aside>

[optimization]: optimization.html

<!--
Some of the material in this chapter will remind you of jlox. The way we resolve
super calls is pretty much the same, though viewed through clox's more complex
mechanism for storing state on the stack. But we have an entirely different,
much faster, way of handling inherited method calls this time around.
-->
本章有些材料会让你想起 jlox。我们解析 super 调用的方式大体相同，只不过透过 clox 在栈上存状态的更复杂机制来看。但这一次，处理继承方法调用的方式完全不同——也快得多。

<!--
-- Inheriting Methods
-->
## 继承方法

<!--
We'll kick things off with method inheritance since it's the simpler piece. To
refresh your memory, Lox inheritance syntax looks like this:
-->
我们从方法继承开场，因为它更简单。温习一下，Lox 的继承语法长这样：

```lox
class Doughnut {
  cook() {
    print "Dunk in the fryer.";
  }
}

class Cruller < Doughnut {
  finish() {
    print "Glaze with icing.";
  }
}
```

<!--
Here, the Cruller class inherits from Doughnut and thus, instances of Cruller
inherit the `cook()` method. I don't know why I'm belaboring this. You know how
inheritance works. Let's start compiling the new syntax.
-->
这里，Cruller 类继承自 Doughnut，于是 Cruller 的实例也继承 `cook()` 方法。我也不知道为什么要啰嗦这些。你知道继承怎么工作。咱们开始编译新语法吧。

^code compile-superclass (2 before, 1 after)

<!--
After we compile the class name, if the next token is a `<`, then we found a
superclass clause. We consume the superclass's identifier token, then call
`variable()`. That function takes the previously consumed token, treats it as a
variable reference, and emits code to load the variable's value. In other words,
it looks up the superclass by name and pushes it onto the stack.
-->
编译完类名之后，若下一个记号是 `<`，就找到了超类子句。我们消费超类的标识符记号，再调用 `variable()`。该函数拿先前消费的记号，当变量引用处理，并发出加载该变量值的代码。换言之：按名字查找超类，并压到栈上。

<!--
After that, we call `namedVariable()` to load the subclass doing the inheriting
onto the stack, followed by an `OP_INHERIT` instruction. That instruction
wires up the superclass to the new subclass. In the last chapter, we defined an
`OP_METHOD` instruction to mutate an existing class object by adding a method to
its method table. This is similar -- the `OP_INHERIT` instruction takes an
existing class and applies the effect of inheritance to it.
-->
随后，我们调用 `namedVariable()`，把正在继承的子类也加载到栈上，再跟一条 `OP_INHERIT` 指令。该指令把超类接到新子类上。上一章我们定义了 `OP_METHOD`：往已有类对象的方法表里加方法来改它。这里类似——`OP_INHERIT` 拿一个已有的类，把继承的效果施加上去。

<!--
In the previous example, when the compiler works through this bit of syntax:
-->
在先前的例子里，编译器处理到这段语法时：

```lox
class Cruller < Doughnut {
```

<!--
The result is this bytecode:
-->
结果是这样的字节码：

<img src="image/superclasses/inherit-stack.png" alt="The series of bytecode instructions for a Cruller class inheriting from Doughnut." />

<!--
Before we implement the new `OP_INHERIT` instruction, we have an edge case to
detect.
-->
在实现新的 `OP_INHERIT` 指令之前，还有一个边界情况要检测。

^code inherit-self (1 before, 1 after)

<!--
<span name="cycle">A</span> class cannot be its own superclass. Unless you have
access to a deranged nuclear physicist and a very heavily modified DeLorean, you
cannot inherit from yourself.
-->
<span name="cycle">一个</span>类不能当自己的超类。除非你能找到一位疯癫的核物理学家，以及一辆大幅改装过的德罗宁，否则你没法继承自己。

<aside name="cycle">

<!--
Interestingly, with the way we implement method inheritance, I don't think
allowing cycles would actually cause any problems in clox. It wouldn't do
anything *useful*, but I don't think it would cause a crash or infinite loop.
-->
有趣的是，以我们实现方法继承的方式，我并不认为允许环会在 clox 里真出问题。它不会做任何*有用*的事，但我想它不会导致崩溃或死循环。

</aside>

<!--
-- Executing inheritance
-->
### 执行继承

<!--
Now onto the new instruction.
-->
现在轮到新指令。

^code inherit-op (1 before, 1 after)

<!--
There are no operands to worry about. The two values we need -- superclass and
subclass -- are both found on the stack. That means disassembling is easy.
-->
没有操作数要操心。我们需要的两个值——超类与子类——都在栈上。所以反汇编很容易。

^code disassemble-inherit (1 before, 1 after)

<!--
The interpreter is where the action happens.
-->
真正干活的是解释器。

^code interpret-inherit (1 before, 1 after)

<!--
From the top of the stack down, we have the subclass then the superclass. We
grab both of those and then do the inherit-y bit. This is where clox takes a
different path than jlox. In our first interpreter, each subclass stored a
reference to its superclass. On method access, if we didn't find the method in
the subclass's method table, we recursed through the inheritance chain looking
at each ancestor's method table until we found it.
-->
从栈顶往下，先是子类，再是超类。我们抓住这两个，然后做那点“继承活”。这里 clox 与 jlox 分道扬镳。在第一台解释器里，每个子类存着指向超类的引用。访问方法时，若子类的方法表里找不到，就沿继承链向上递归，查看每个祖先的方法表，直到找到为止。

<!--
For example, calling `cook()` on an instance of Cruller sends jlox on this
journey:
-->
例如，在 Cruller 实例上调用 `cook()`，会让 jlox 走上这段旅程：

<img src="image/superclasses/jlox-resolve.png" alt="Resolving a call to cook() in an instance of Cruller means walking the superclass chain." />

<!--
That's a lot of work to perform during method *invocation* time. It's slow, and
worse, the farther an inherited method is up the ancestor chain, the slower it
gets. Not a great performance story.
-->
这在方法*调用*时要干的活可不少。慢，更糟的是：继承来的方法在祖先链上越靠上，就越慢。不算什么好性能故事。

<!--
The new approach is much faster. When the subclass is declared, we copy all of
the inherited class's methods down into the subclass's own method table. Later,
when *calling* a method, any method inherited from a superclass will be found
right in the subclass's own method table. There is no extra runtime work needed
for inheritance at all. By the time the class is declared, the work is done.
This means inherited method calls are exactly as fast as normal method calls --
a <span name="two">single</span> hash table lookup.
-->
新做法快得多。子类声明时，我们把被继承类的全部方法向下复制进子类自己的方法表。之后*调用*方法时，任何从超类继承来的方法，就在子类自己的方法表里。继承完全不需要额外的运行时工作。类声明完成时，活已经干完了。这意味着继承方法调用与普通方法调用一样快——<span name="two">一次</span>哈希表查找。

<img src="image/superclasses/clox-resolve.png" alt="Resolving a call to cook() in an instance of Cruller which has the method in its own method table." />

<aside name="two">

<!--
Well, two hash table lookups, I guess. Because first we have to make sure a
field on the instance doesn't shadow the method.
-->
好吧，大概是两次哈希表查找。因为我们得先确认实例上的字段没有遮蔽该方法。

</aside>

<!--
I've sometimes heard this technique called "copy-down inheritance". It's simple
and fast, but, like most optimizations, you get to use it only under certain
constraints. It works in Lox because Lox classes are *closed*. Once a class
declaration is finished executing, the set of methods for that class can never
change.
-->
我有时听人把这招叫“向下复制（copy-down）继承”。简单又快，但像多数优化一样，只有在特定约束下才能用。它在 Lox 里成立，是因为 Lox 的类是*封闭*的。一旦类声明执行完毕，该类的方法集合就永远不能再变。

<!--
In languages like Ruby, Python, and JavaScript, it's possible to <span
name="monkey">crack</span> open an existing class and jam some new methods into
it or even remove them. That would break our optimization because if those
modifications happened to a superclass *after* the subclass declaration
executed, the subclass would not pick up those changes. That breaks a user's
expectation that inheritance always reflects the current state of the
superclass.
-->
在 Ruby、Python、JavaScript 这类语言里，可以<span name="monkey">撬开</span>已有的类，塞进新方法，甚至删掉方法。那会弄坏我们的优化：若这些修改发生在子类声明执行*之后*，子类不会跟上那些变化。这违背了用户的预期——继承应始终反映超类的当前状态。

<aside name="monkey">

<!--
As you can imagine, changing the set of methods a class defines imperatively at
runtime can make it hard to reason about a program. It is a very powerful tool,
but also a dangerous tool.

Those who find this tool maybe a little *too* dangerous gave it the unbecoming
name "monkey patching", or the even less decorous "duck punching".
-->
可想而知，在运行时命令式地改动类定义的方法集合，会让程序很难推理。这是非常强大的工具，也是危险的工具。

觉得这工具或许有点*太*危险的人，给了它不太体面的名字：“猴子补丁”（monkey patching），或更不雅的“打鸭子”（duck punching）。

<img src="image/superclasses/monkey.png" alt="A monkey with an eyepatch, naturally." />

</aside>

<!--
Fortunately for us (but not for users who like the feature, I guess), Lox
doesn't let you patch monkeys or punch ducks, so we can safely apply this
optimization.
-->
对我们来说幸运（对喜欢这特性的用户大概不幸）：Lox 不许你给猴子打补丁或揍鸭子，所以我们可以安全地用上这项优化。

<!--
What about method overrides? Won't copying the superclass's methods into the
subclass's method table clash with the subclass's own methods? Fortunately, no.
We emit the `OP_INHERIT` after the `OP_CLASS` instruction that creates the
subclass but before any method declarations and `OP_METHOD` instructions have
been compiled. At the point that we copy the superclass's methods down, the
subclass's method table is empty. Any methods the subclass overrides will
overwrite those inherited entries in the table.
-->
那方法覆盖呢？把超类方法复制进子类方法表，不会和子类自己的方法撞车吗？幸运的是，不会。我们在创建子类的 `OP_CLASS` 之后、任何方法声明与 `OP_METHOD` 指令编译之前发出 `OP_INHERIT`。向下复制超类方法时，子类的方法表还是空的。子类覆盖的任何方法，都会覆盖表里那些继承来的条目。

<!--
-- Invalid superclasses
-->
### 无效的超类

<!--
Our implementation is simple and fast, which is just the way I like my VM code.
But it's not robust. Nothing prevents a user from inheriting from an object that
isn't a class at all:
-->
我们的实现简单又快——正是我喜欢的虚拟机代码风格。但它还不稳健。没有什么能阻止用户从一个根本不是类的对象继承：

```lox
var NotClass = "So not a class";
class OhNo < NotClass {}
```

<!--
Obviously, no self-respecting programmer would write that, but we have to guard
against potential Lox users who have no self respect. A simple runtime check
fixes that.
-->
显然，有自尊心的程序员不会写那种东西，但我们得防备那些可能没有自尊心的 Lox 用户。一个简单的运行时检查就能搞定。

^code inherit-non-class (1 before, 1 after)

<!--
If the value we loaded from the identifier in the superclass clause isn't an
ObjClass, we report a runtime error to let the user know what we think of them
and their code.
-->
若从超类子句里那个标识符加载出的值不是 ObjClass，我们就报告运行时错误，好让用户知道我们对他们及其代码怎么看。

<!--
-- Storing Superclasses
-->
## 存储超类

<!--
Did you notice that when we added method inheritance, we didn't actually add any
reference from a subclass to its superclass? After we copy the inherited methods
over, we forget the superclass entirely. We don't need to keep a handle on the
superclass, so we don't.
-->
你注意到了吗：加上方法继承时，我们其实并没有给子类加指向超类的引用？复制完继承方法后，我们把超类彻底忘掉了。我们不需要握着超类的句柄，所以就不握。

<!--
That won't be sufficient to support super calls. Since a subclass <span
name="may">may</span> override the superclass method, we need to be able to get
our hands on superclass method tables. Before we get to that mechanism, I want
to refresh your memory on how super calls are statically resolved.
-->
这对支持 super 调用还不够。既然子类<span name="may">可能</span>覆盖超类方法，我们就需要能摸到超类的方法表。在讲那套机制之前，我想先帮你温习一下：super 调用是如何静态解析的。

<aside name="may">

<!--
"May" might not be a strong enough word. Presumably the method *has* been
overridden. Otherwise, why are you bothering to use `super` instead of just
calling it directly?
-->
“可能”也许还不够重。按理说方法*已经被*覆盖了。否则你干嘛费劲用 `super`，而不是直接调用？

</aside>

<!--
Back in the halcyon days of jlox, I showed you [this tricky example][example] to
explain the way super calls are dispatched:
-->
在 jlox 的美好旧日里，我给你看过[这个棘手例子][example]，用来解释 super 调用如何分派：

[example]: inheritance.html#semantics

```lox
class A {
  method() {
    print "A method";
  }
}

class B < A {
  method() {
    print "B method";
  }

  test() {
    super.method();
  }
}

class C < B {}

C().test();
```

<!--
Inside the body of the `test()` method, `this` is an instance of C. If super
calls were resolved relative to the superclass of the *receiver*, then we would
look in C's superclass, B. But super calls are resolved relative to the
superclass of the *surrounding class where the super call occurs*. In this case,
we are in B's `test()` method, so the superclass is A, and the program should
print "A method".
-->
在 `test()` 方法体里，`this` 是 C 的实例。若 super 调用相对于*接收者*的超类解析，我们会看 C 的超类 B。但 super 调用是相对于*发生该调用的外围类*的超类解析的。这里我们在 B 的 `test()` 里，所以超类是 A，程序应打印 `"A method"`。

<!--
This means that super calls are not resolved dynamically based on the runtime
instance. The superclass used to look up the method is a static -- practically
lexical -- property of where the call occurs. When we added inheritance to jlox,
we took advantage of that static aspect by storing the superclass in the same
Environment structure we used for all lexical scopes. Almost as if the
interpreter saw the above program like this:
-->
这意味着 super 调用并不基于运行时实例动态解析。用来查找方法的超类，是调用发生位置的静态——近乎词法——属性。给 jlox 加继承时，我们利用了这点静态性：把超类存进与所有词法作用域共用的 Environment 结构。几乎像是解释器把上面的程序看成这样：

```lox
class A {
  method() {
    print "A method";
  }
}

var Bs_super = A;
class B < A {
  method() {
    print "B method";
  }

  test() {
    runtimeSuperCall(Bs_super, "method");
  }
}

var Cs_super = B;
class C < B {}

C().test();
```

<!--
Each subclass has a hidden variable storing a reference to its superclass.
Whenever we need to perform a super call, we access the superclass from that
variable and tell the runtime to start looking for methods there.
-->
每个子类有一个隐藏变量，存着指向其超类的引用。每当需要做 super 调用，我们就从该变量取出超类，并告诉运行时从那里开始找方法。

<!--
We'll take the same path with clox. The difference is that instead of jlox's
heap-allocated Environment class, we have the bytecode VM's value stack and
upvalue system. The machinery is a little different, but the overall effect is
the same.
-->
clox 走同一条路。差别在于：不是 jlox 堆上分配的 Environment 类，而是字节码虚拟机的值栈与上值系统。机械装置略有不同，整体效果一样。

<!--
-- A superclass local variable
-->
### 超类局部变量

<!--
Our compiler already emits code to load the superclass onto the stack. Instead
of leaving that slot as a temporary, we create a new scope and make it a local
variable.
-->
编译器已经会发出把超类加载到栈上的代码。我们不把那个槽位留作临时量，而是新建一个作用域，让它成为局部变量。

^code superclass-variable (2 before, 2 after)

<!--
Creating a new lexical scope ensures that if we declare two classes in the same
scope, each has a different local slot to store its superclass. Since we always
name this variable "super", if we didn't make a scope for each subclass, the
variables would collide.
-->
新建词法作用域，保证若在同一作用域里声明两个类，各自有不同的局部槽位存放超类。我们总把这变量叫 `"super"`，若不为每个子类单独建作用域，变量就会撞名。

<!--
We name the variable "super" for the same reason we use "this" as the name of
the hidden local variable that `this` expressions resolve to: "super" is a
reserved word, which guarantees the compiler's hidden variable won't collide
with a user-defined one.
-->
变量叫 `"super"`，理由与我们把 `this` 表达式解析到的隐藏局部变量叫 `"this"` 相同：`"super"` 是保留字，保证编译器的隐藏变量不会与用户定义的撞车。

<!--
The difference is that when compiling `this` expressions, we conveniently have a
token sitting around whose lexeme is "this". We aren't so lucky here. Instead,
we add a little helper function to create a synthetic token for the given <span
name="constant">constant</span> string.
-->
差别在于：编译 `this` 表达式时，手头碰巧有个词素是 `"this"` 的记号。这里没那么走运。于是我们加一个小辅助函数，为给定的<span name="constant">常量</span>字符串创建合成记号。

^code synthetic-token

<aside name="constant" class="bottom">

<!--
I say "constant string" because tokens don't do any memory management of their
lexeme. If we tried to use a heap-allocated string for this, we'd end up leaking
memory because it never gets freed. But the memory for C string literals lives
in the executable's constant data section and never needs to be freed, so we're
fine.
-->
我说“常量字符串”，是因为记号并不管理其词素的内存。若为此用堆分配的字符串，就会泄漏——它永远不会被释放。而 C 字符串字面量的内存在可执行文件的常量数据段里，永远不必释放，所以我们没事。

</aside>

<!--
Since we opened a local scope for the superclass variable, we need to close it.
-->
既然为超类变量打开了局部作用域，就得关上它。

^code end-superclass-scope (1 before, 2 after)

<!--
We pop the scope and discard the "super" variable after compiling the class body
and its methods. That way, the variable is accessible in all of the methods of
the subclass. It's a somewhat pointless optimization, but we create the scope
only if there *is* a superclass clause. Thus we need to close the scope only if
there is one.
-->
编译完类体及其方法后，我们弹出作用域并丢弃 `"super"` 变量。这样，该变量在子类的全部方法里都可访问。这是个略显无聊的优化，但我们只在*有*超类子句时才创建作用域。因此也只在有时才需要关闭。

<!--
To track that, we could declare a little local variable in `classDeclaration()`.
But soon, other functions in the compiler will need to know whether the
surrounding class is a subclass or not. So we may as well give our future selves
a hand and store this fact as a field in the ClassCompiler now.
-->
为跟踪这一点，可以在 `classDeclaration()` 里声明一个小局部变量。但很快，编译器里的其他函数也需要知道外围类是不是子类。所以不妨现在就帮未来的自己一把：把这事实存成 ClassCompiler 的一个字段。

^code has-superclass (2 before, 1 after)

<!--
When we first initialize a ClassCompiler, we assume it is not a subclass.
-->
初次初始化 ClassCompiler 时，我们假定它不是子类。

^code init-has-superclass (1 before, 1 after)

<!--
Then, if we see a superclass clause, we know we are compiling a subclass.
-->
然后，若看到超类子句，就知道我们在编译一个子类。

^code set-has-superclass (1 before, 1 after)

<!--
This machinery gives us a mechanism at runtime to access the superclass object
of the surrounding subclass from within any of the subclass's methods -- simply
emit code to load the variable named "super". That variable is a local outside
of the method body, but our existing upvalue support enables the VM to capture
that local inside the body of the method or even in functions nested inside that
method.
-->
这套机械装置给了我们运行时机制：在子类的任意方法里访问外围子类的超类对象——只需发出加载名为 `"super"` 的变量的代码。该变量是方法体之外的局部量，但已有的上值支持让虚拟机能在方法体内部、甚至嵌在该方法里的函数中捕获它。

<!--
-- Super Calls
-->
## 超类调用

<!--
With that runtime support in place, we are ready to implement super calls. As
usual, we go front to back, starting with the new syntax. A super call <span
name="last">begins</span>, naturally enough, with the `super` keyword.
-->
有了运行时支持，我们就可以实现 super 调用了。照例从前到后，从新语法开始。super 调用自然而然地<span name="last">始于</span> `super` 关键字。

<aside name="last">

<!--
This is it, friend. The very last entry you'll add to the parsing table.
-->
就是它了，朋友。你往解析表里加的最后一项。

</aside>

^code table-super (1 before, 1 after)

<!--
When the expression parser lands on a `super` token, control jumps to a new
parsing function which starts off like so:
-->
当表达式解析器落到 `super` 记号上，控制跳到一个新的解析函数，开头如下：

^code super

<!--
This is pretty different from how we compiled `this` expressions. Unlike `this`,
a `super` <span name="token">token</span> is not a standalone expression.
Instead, the dot and method name following it are inseparable parts of the
syntax. However, the parenthesized argument list is separate. As with normal
method access, Lox supports getting a reference to a superclass method as a
closure without invoking it:
-->
这与编译 `this` 表达式相当不同。不像 `this`，一个 `super` <span name="token">记号</span>不是独立表达式。相反，后面的点和方法名是语法不可分割的部分。不过，括号里的参数列表是分开的。与普通方法访问一样，Lox 支持把超类方法作为闭包引用拿到，而不调用它：

<aside name="token">

<!--
Hypothetical question: If a bare `super` token *was* an expression, what kind of
object would it evaluate to?
-->
假想问题：若光秃秃的 `super` 记号*是*一个表达式，它会求值成什么样的对象？

</aside>

```lox
class A {
  method() {
    print "A";
  }
}

class B < A {
  method() {
    var closure = super.method;
    closure(); // Prints "A".
  }
}
```

<!--
In other words, Lox doesn't really have super *call* expressions, it has super
*access* expressions, which you can choose to immediately invoke if you want. So
when the compiler hits a `super` token, we consume the subsequent `.` token and
then look for a method name. Methods are looked up dynamically, so we use
`identifierConstant()` to take the lexeme of the method name token and store it
in the constant table just like we do for property access expressions.
-->
换言之，Lox 其实没有 super *调用*表达式，它有的是 super *访问*表达式——你愿意的话可以立刻调用。所以编译器碰到 `super` 记号时，我们消费随后的 `.`，再找方法名。方法是动态查找的，于是我们用 `identifierConstant()` 取方法名记号的词素，存进常量表——与属性访问表达式一样。

<!--
Here is what the compiler does after consuming those tokens:
-->
消费完那些记号后，编译器做这些事：

^code super-get (1 before, 1 after)

<!--
In order to access a *superclass method* on *the current instance*, the runtime
needs both the receiver *and* the superclass of the surrounding method's class.
The first `namedVariable()` call generates code to look up the current receiver
stored in the hidden variable "this" and push it onto the stack. The second
`namedVariable()` call emits code to look up the superclass from its "super"
variable and push that on top.
-->
要在*当前实例*上访问*超类方法*，运行时既需要接收者，*也*需要外围方法所属类的超类。第一次 `namedVariable()` 调用生成代码：查找藏在隐藏变量 `"this"` 里的当前接收者并压栈。第二次 `namedVariable()` 发出代码：从其 `"super"` 变量查找超类，再压到栈顶。

<!--
Finally, we emit a new `OP_GET_SUPER` instruction with an operand for the
constant table index of the method name. That's a lot to hold in your head. To
make it tangible, consider this example program:
-->
最后，我们发出一条新的 `OP_GET_SUPER` 指令，操作数是方法名在常量表中的索引。要记在脑子里的东西不少。为了更具体，看看这个示例程序：

```lox
class Doughnut {
  cook() {
    print "Dunk in the fryer.";
    this.finish("sprinkles");
  }

  finish(ingredient) {
    print "Finish with " + ingredient;
  }
}

class Cruller < Doughnut {
  finish(ingredient) {
    // No sprinkles, always icing.
    super.finish("icing");
  }
}
```

<!--
The bytecode emitted for the `super.finish("icing")` expression looks and works
like this:
-->
为 `super.finish("icing")` 表达式发出的字节码看起来、工作起来是这样的：

<img src="image/superclasses/super-instructions.png" alt="The series of bytecode instructions for calling super.finish()." />

<!--
The first three instructions give the runtime access to the three pieces of
information it needs to perform the super access:

1.  The first instruction loads **the instance** onto the stack.

2.  The second instruction loads **the superclass where the method is
    resolved**.

3.  Then the new `OP_GET_SUPER` instuction encodes **the name of the method to
    access** as an operand.

The remaining instructions are the normal bytecode for evaluating an argument
list and calling a function.
-->
前三条指令让运行时拿到做 super 访问所需的三块信息：

1.  第一条指令把**实例**加载到栈上。

2.  第二条指令加载**解析方法所在的超类**。

3.  然后新的 `OP_GET_SUPER` 指令把**要访问的方法名**编码为操作数。

其余指令是求值参数列表并调用函数的普通字节码。

<!--
We're almost ready to implement the new `OP_GET_SUPER` instruction in the
interpreter. But before we do, the compiler has some errors it is responsible
for reporting.
-->
我们几乎可以在解释器里实现新的 `OP_GET_SUPER` 了。但在此之前，编译器还有一些它负责报告的错误。

^code super-errors (1 before, 1 after)

<!--
A super call is meaningful only inside the body of a method (or in a function
nested inside a method), and only inside the method of a class that has a
superclass. We detect both of these cases using the value of `currentClass`. If
that's `NULL` or points to a class with no superclass, we report those errors.
-->
super 调用只在方法体里（或嵌在方法里的函数里）有意义，且只在有超类的类的方法里。我们用 `currentClass` 的值检测这两种情况。若它是 `NULL`，或指向没有超类的类，就报告那些错误。

<!--
-- Executing super accesses
-->
### 执行 super 访问

<!--
Assuming the user didn't put a `super` expression where it's not allowed, their
code passes from the compiler over to the runtime. We've got ourselves a new
instruction.
-->
假定用户没有把 `super` 表达式放在不允许的地方，他们的代码就从编译器交到运行时。我们有了一条新指令。

^code get-super-op (1 before, 1 after)

<!--
We disassemble it like other opcodes that take a constant table index operand.
-->
我们像其他带常量表索引操作数的操作码一样反汇编它。

^code disassemble-get-super (1 before, 1 after)

<!--
You might anticipate something harder, but interpreting the new instruction is
similar to executing a normal property access.
-->
你或许以为会更难，但解释这条新指令与执行普通属性访问相似。

^code interpret-get-super (1 before, 1 after)

<!--
As with properties, we read the method name from the
constant table. Then we pass that to `bindMethod()` which looks up the method in
the given class's method table and creates an ObjBoundMethod to bundle the
resulting closure to the current instance.
-->
与属性一样，我们从常量表读出方法名。再把它传给 `bindMethod()`：在给定类的方法表里查找方法，并创建一个 ObjBoundMethod，把得到的闭包与当前实例捆在一起。

<!--
The key <span name="field">difference</span> is *which* class we pass to
`bindMethod()`. With a normal property access, we use the ObjInstances's own
class, which gives us the dynamic dispatch we want. For a super call, we don't
use the instance's class. Instead, we use the statically resolved superclass of
the containing class, which the compiler has conveniently ensured is sitting on
top of the stack waiting for us.
-->
关键<span name="field">差异</span>在于我们把*哪个*类传给 `bindMethod()`。普通属性访问用 ObjInstance 自己的类，这给我们想要的动态分派。对 super 调用，我们不用实例的类。相反，我们用包含类经静态解析得到的超类——编译器已方便地确保它正坐在栈顶等我们。

<!--
We pop that superclass and pass it to `bindMethod()`, which correctly skips over
any overriding methods in any of the subclasses between that superclass and the
instance's own class. It also correctly includes any methods inherited by the
superclass from any of *its* superclasses.
-->
我们弹出那个超类并传给 `bindMethod()`，它会正确跳过该超类与实例自身类之间任何子类里的覆盖方法。它也会正确包含超类从*它自己的*超类继承来的任何方法。

<!--
The rest of the behavior is the same. Popping the superclass leaves the instance
at the top of the stack. When `bindMethod()` succeeds, it pops the instance and
pushes the new bound method. Otherwise, it reports a runtime error and returns
`false`. In that case, we abort the interpreter.
-->
其余行为相同。弹出超类后，实例留在栈顶。`bindMethod()` 成功时，弹出实例并压入新的绑定方法。否则报告运行时错误并返回 `false`。那种情况下，我们中止解释器。

<aside name="field">

<!--
Another difference compared to `OP_GET_PROPERTY` is that we don't try to look
for a shadowing field first. Fields are not inherited, so `super` expressions
always resolve to methods.

If Lox were a prototype-based language that used *delegation* instead of
*inheritance*, then instead of one *class* inheriting from another *class*,
instances would inherit from ("delegate to") other instances. In that case,
fields *could* be inherited, and we would need to check for them here.
-->
与 `OP_GET_PROPERTY` 相比还有一点不同：我们不会先找可能遮蔽的字段。字段不被继承，所以 `super` 表达式总是解析到方法。

若 Lox 是基于原型、用*委托*而非*继承*的语言，那就不是一个*类*继承另一个*类*，而是实例继承自（“委托给”）其他实例。那种情况下，字段*可以*被继承，我们这里就得检查它们。

</aside>

<!--
-- Faster super calls
-->
### 更快的超类调用

<!--
We have superclass method accesses working now. And since the returned object is
an ObjBoundMethod that you can then invoke, we've got super *calls* working too.
Just like last chapter, we've reached a point where our VM has the complete,
correct semantics.
-->
超类方法访问现在能工作了。而返回对象是可再调用的 ObjBoundMethod，所以 super *调用*也通了。和上一章一样，我们到了虚拟机具备完整、正确语义的节点。

<!--
But, also like last chapter, it's pretty slow. Again, we're heap allocating an
ObjBoundMethod for each super call even though most of the time the very next
instruction is an `OP_CALL` that immediately unpacks that bound method, invokes
it, and then discards it. In fact, this is even more likely to be true for
super calls than for regular method calls. At least with method calls there is
a chance that the user is actually invoking a function stored in a field. With
super calls, you're *always* looking up a method. The only question is whether
you invoke it immediately or not.
-->
但同样像上一章，它相当慢。我们再次为每次 super 调用在堆上分配 ObjBoundMethod，尽管多数时候下一条指令就是 `OP_CALL`：立刻拆开那个绑定方法、调用它，然后丢掉。事实上，这对 super 调用比对普通方法调用更可能成立。至少普通方法调用还有可能是在调字段里存的函数。而 super 调用，你*总是*在查方法。唯一的问题是：要不要立刻调用。

<!--
The compiler can certainly answer that question for itself if it sees a left
parenthesis after the superclass method name, so we'll go ahead and perform the
same optimization we did for method calls. Take out the two lines of code that
load the superclass and emit `OP_GET_SUPER`, and replace them with this:
-->
若编译器在超类方法名后看到左括号，当然能自己回答这个问题，于是我们照方法调用那一套做同样的优化。拿掉加载超类并发出 `OP_GET_SUPER` 的那两行，换成这些：

^code super-invoke (1 before, 1 after)

<!--
Now before we emit anything, we look for a parenthesized argument list. If we
find one, we compile that. Then we load the superclass. After that, we emit a
new `OP_SUPER_INVOKE` instruction. This <span
name="superinstruction">superinstruction</span> combines the behavior of
`OP_GET_SUPER` and `OP_CALL`, so it takes two operands: the constant table index
of the method name to look up and the number of arguments to pass to it.
-->
现在发出任何东西之前，我们先找带括号的参数列表。若找到，就编译它。然后加载超类。之后发出一条新的 `OP_SUPER_INVOKE` 指令。这条<span name="superinstruction">超指令</span>合并了 `OP_GET_SUPER` 与 `OP_CALL` 的行为，因此带两个操作数：要查找的方法名在常量表中的索引，以及传给它的参数个数。

<aside name="superinstruction">

<!--
This is a particularly *super* superinstruction, if you get what I'm saying.
I... I'm sorry for this terrible joke.
-->
这可是一条特别 *super* 的超指令，懂我意思吧。我……抱歉开了这么烂的玩笑。

</aside>

<!--
Otherwise, if we don't find a `(`, we continue to compile the expression as a
super access like we did before and emit an `OP_GET_SUPER`.
-->
否则，若找不到 `(`，就继续像以前那样把表达式编译成 super 访问，并发出 `OP_GET_SUPER`。

<!--
Drifting down the compilation pipeline, our first stop is a new instruction.
-->
顺着编译流水线往下漂，第一站是一条新指令。

^code super-invoke-op (1 before, 1 after)

<!--
And just past that, its disassembler support.
-->
紧接着是它的反汇编支持。

^code disassemble-super-invoke (1 before, 1 after)

<!--
A super invocation instruction has the same set of operands as `OP_INVOKE`, so
we reuse the same helper to disassemble it. Finally, the pipeline dumps us into
the interpreter.
-->
超类调用指令与 `OP_INVOKE` 有同一套操作数，所以我们复用同一个辅助函数来反汇编。最后，流水线把我们扔进解释器。

^code interpret-super-invoke (2 before, 1 after)

<!--
This handful of code is basically our implementation of `OP_INVOKE` mixed
together with a dash of `OP_GET_SUPER`. There are some differences in how the
stack is organized, though. With an unoptimized super call, the superclass is
popped and replaced by the ObjBoundMethod for the resolved function *before* the
arguments to the call are executed. This ensures that by the time the `OP_CALL`
is executed, the bound method is *under* the argument list, where the runtime
expects it to be for a closure call.
-->
这把代码基本上是 `OP_INVOKE` 的实现，再掺一撮 `OP_GET_SUPER`。不过栈的组织有些不同。未优化的 super 调用里，超类在调用参数执行*之前*就被弹出，换成解析出的函数对应的 ObjBoundMethod。这保证执行 `OP_CALL` 时，绑定方法在参数列表*下面*——运行时对闭包调用所期望的位置。

<!--
With our optimized instructions, things are shuffled a bit:
-->
用上优化指令后，事情略有打乱：

<img src="image/superclasses/super-invoke.png" class="wide" alt="The series of bytecode instructions for calling super.finish() using OP_SUPER_INVOKE." />

<!--
Now resolving the superclass method is part of the *invocation*, so the
arguments need to already be on the stack at the point that we look up the
method. This means the superclass object is on top of the arguments.
-->
现在解析超类方法是*调用*的一部分，所以查找方法时，参数必须已经在栈上。这意味着超类对象在参数之上。

<!--
Aside from that, the behavior is roughly the same as an `OP_GET_SUPER` followed
by an `OP_CALL`. First, we pull out the method name and argument count operands.
Then we pop the superclass off the top of the stack so that we can look up the
method in its method table. This conveniently leaves the stack set up just right
for a method call.
-->
除此之外，行为大致等同于 `OP_GET_SUPER` 后再跟 `OP_CALL`。先取出方法名与参数个数操作数。再从栈顶弹出超类，以便在其方法表里查找方法。这恰好把栈摆成适合方法调用的样子。

<!--
We pass the superclass, method name, and argument count to our existing
`invokeFromClass()` function. That function looks up the given method on the
given class and attempts to create a call to it with the given arity. If a
method could not be found, it returns `false`, and we bail out of the
interpreter. Otherwise, `invokeFromClass()` pushes a new CallFrame onto the call
stack for the method's closure. That invalidates the interpreter's cached
CallFrame pointer, so we refresh `frame`.
-->
我们把超类、方法名和参数个数传给已有的 `invokeFromClass()`。该函数在给定类上查找给定方法，并尝试以给定元数创建对它的调用。若找不到方法，返回 `false`，我们退出解释器。否则，`invokeFromClass()` 为方法的闭包往调用栈压入一个新的 CallFrame。这会使解释器缓存的 CallFrame 指针失效，所以我们刷新 `frame`。

<!--
-- A Complete Virtual Machine
-->
## 完整的虚拟机

<!--
Take a look back at what we've created. By my count, we wrote around 2,500 lines
of fairly clean, straightforward C. That little program contains a complete
implementation of the -- quite high-level! -- Lox language, with a whole
precedence table full of expression types and a suite of control flow
statements. We implemented variables, functions, closures, classes, fields,
methods, and inheritance.
-->
回头看看我们造出了什么。按我的数，我们写了大约 2500 行相当干净、直白的 C。那一小段程序里装着——相当高阶的！——Lox 语言的完整实现：整张优先级表塞满表达式类型，还有一套控制流语句。我们实现了变量、函数、闭包、类、字段、方法，以及继承。

<!--
Even more impressive, our implementation is portable to any platform with a C
compiler, and is fast enough for real-world production use. We have a
single-pass bytecode compiler, a tight virtual machine interpreter for our
internal instruction set, compact object representations, a stack for storing
variables without heap allocation, and a precise garbage collector.
-->
更了不起的是：实现可移植到任何有 C 编译器的平台，而且快到足以用于真实生产。我们有单遍字节码编译器、针对内部指令集的紧凑虚拟机解释器、紧凑的对象表示、无需堆分配即可存变量的栈，以及精确的垃圾回收器。

<!--
If you go out and start poking around in the implementations of Lua, Python, or
Ruby, you will be surprised by how much of it now looks familiar to you. You
have seriously leveled up your knowledge of how programming languages work,
which in turn gives you a deeper understanding of programming itself. It's like
you used to be a race car driver, and now you can pop the hood and repair the
engine too.
-->
若你出去翻翻 Lua、Python 或 Ruby 的实现，会惊讶于其中多少东西现在看起来眼熟。你对编程语言如何工作的认识已认真升了一级，而这又让你对编程本身有更深理解。就像你从前是赛车手，现在也能掀开引擎盖修发动机了。

<!--
You can stop here if you like. The two implementations of Lox you have are
complete and full featured. You built the car and can drive it wherever you want
now. But if you are looking to have more fun tuning and tweaking for even
greater performance out on the track, there is one more chapter. We don't add
any new capabilities, but we roll in a couple of classic optimizations to
squeeze even more perf out. If that sounds fun, [keep reading][opt]...
-->
愿意的话，你可以停在这里。你手里的两份 Lox 实现都已完整且功能齐全。车造好了，想开哪儿就开哪儿。但若还想在赛道上调校、压榨出更多性能找乐子，还有一章。我们不加任何新能力，只塞进几项经典优化，再挤一点性能。若这听起来好玩，[继续往下读][opt]……

[opt]: optimization.html

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
1.  A tenet of object-oriented programming is that a class should ensure new
    objects are in a valid state. In Lox, that means defining an initializer
    that populates the instance's fields. Inheritance complicates invariants
    because the instance must be in a valid state according to all of the
    classes in the object's inheritance chain.

    The easy part is remembering to call `super.init()` in each subclass's
    `init()` method. The harder part is fields. There is nothing preventing two
    classes in the inheritance chain from accidentally claiming the same field
    name. When this happens, they will step on each other's fields and possibly
    leave you with an instance in a broken state.

    If Lox was your language, how would you address this, if at all? If you
    would change the language, implement your change.

2.  Our copy-down inheritance optimization is valid only because Lox does not
    permit you to modify a class's methods after its declaration. This means we
    don't have to worry about the copied methods in the subclass getting out of
    sync with later changes to the superclass.

    Other languages, like Ruby, *do* allow classes to be modified after the
    fact. How do implementations of languages like that support class
    modification while keeping method resolution efficient?

3.  In the [jlox chapter on inheritance][inheritance], we had a challenge to
    implement the BETA language's approach to method overriding. Solve the
    challenge again, but this time in clox. Here's the description of the
    previous challenge:

    In Lox, as in most other object-oriented languages, when looking up a
    method, we start at the bottom of the class hierarchy and work our way up --
    a subclass's method is preferred over a superclass's. In order to get to the
    superclass method from within an overriding method, you use `super`.

    The language [BETA][] takes the [opposite approach][inner]. When you call a
    method, it starts at the *top* of the class hierarchy and works *down*. A
    superclass method wins over a subclass method. In order to get to the
    subclass method, the superclass method can call `inner`, which is sort of
    like the inverse of `super`. It chains to the next method down the
    hierarchy.

    The superclass method controls when and where the subclass is allowed to
    refine its behavior. If the superclass method doesn't call `inner` at all,
    then the subclass has no way of overriding or modifying the superclass's
    behavior.

    Take out Lox's current overriding and `super` behavior, and replace it with
    BETA's semantics. In short:

    *   When calling a method on a class, the method *highest* on the
        class's inheritance chain takes precedence.

    *   Inside the body of a method, a call to `inner` looks for a method with
        the same name in the nearest subclass along the inheritance chain
        between the class containing the `inner` and the class of `this`. If
        there is no matching method, the `inner` call does nothing.

    For example:

    ```lox
    class Doughnut {
      cook() {
        print "Fry until golden brown.";
        inner();
        print "Place in a nice box.";
      }
    }

    class BostonCream < Doughnut {
      cook() {
        print "Pipe full of custard and coat with chocolate.";
      }
    }

    BostonCream().cook();
    ```

    This should print:

    ```text
    Fry until golden brown.
    Pipe full of custard and coat with chocolate.
    Place in a nice box.
    ```

    Since clox is about not just implementing Lox, but doing so with good
    performance, this time around try to solve the challenge with an eye towards
    efficiency.
-->
1.  面向对象编程的一条信条是：类应确保新对象处于有效状态。在 Lox 里，这意味着定义一个填充实例字段的初始化器。继承让不变量更复杂，因为实例必须相对对象继承链上的*所有*类都处于有效状态。

    容易的部分是记得在每个子类的 `init()` 里调用 `super.init()`。更难的是字段。没有什么能阻止继承链上两个类碰巧声称同一字段名。一旦发生，它们会踩到彼此的字段，可能留下一个损坏状态的实例。

    若 Lox 是你的语言，你会如何处理这事（若要处理的话）？若你会改语言，实现你的改动。

2.  我们的向下复制（copy-down）继承优化之所以成立，只因为 Lox 不允许在类声明之后修改其方法。这意味着我们不必担心子类里复制来的方法与超类后来的改动不同步。

    其他语言，如 Ruby，*确实*允许事后修改类。这类语言的实现如何在支持类修改的同时，仍保持高效的方法解析？

3.  在 [jlox 的继承章][inheritance]里，我们有一道挑战：实现 BETA 语言的方法覆盖方式。再解一次，这次用 clox。先前挑战的描述如下：

    在 Lox 里，与多数其他面向对象语言一样，查找方法时我们从类层次底部向上走——子类方法优先于超类方法。要从覆盖方法内部到达超类方法，用 `super`。

    语言 [BETA][] 采取[相反做法][inner]。调用方法时，它从类层次的*顶部*开始*向下*走。超类方法胜过子类方法。要到达子类方法，超类方法可以调用 `inner`，有点像 `super` 的逆。它链到层次中下一个更靠下的方法。

    超类方法控制子类何时、何处被允许细化行为。若超类方法根本不调用 `inner`，子类就无法覆盖或修改超类的行为。

    去掉 Lox 当前的覆盖与 `super` 行为，换成 BETA 的语义。简言之：

    *   在类上调用方法时，类继承链上*最高*的那个方法优先。

    *   在方法体里，对 `inner` 的调用沿继承链，在含 `inner` 的类与 `this` 的类之间，查找最近子类中同名方法。若没有匹配方法，`inner` 调用什么也不做。

    例如：

    ```lox
    class Doughnut {
      cook() {
        print "Fry until golden brown.";
        inner();
        print "Place in a nice box.";
      }
    }

    class BostonCream < Doughnut {
      cook() {
        print "Pipe full of custard and coat with chocolate.";
      }
    }

    BostonCream().cook();
    ```

    应打印：

    ```text
    Fry until golden brown.
    Pipe full of custard and coat with chocolate.
    Place in a nice box.
    ```

    既然 clox 不只是实现 Lox，还要以良好性能实现，这一次解题时请着眼于效率。

[inheritance]: inheritance.html
[inner]: http://journal.stuffwithstuff.com/2012/12/19/the-impoliteness-of-overriding-methods/
[beta]: https://beta.cs.au.dk/

</div>
