# 类

> 一个人若尚未对其本性获得彻底的了解，便无权去爱它或恨它。深厚的爱，源于对所爱之物的博大认识；倘若你只识得皮毛，那你也只能爱它一二，甚至全然无法去爱。
>
> <cite>列奥纳多·达·芬奇</cite>

我们一路走到了第十一章，栖身于你机器上的那款解释器，几乎已是一门完整无缺的脚本语言了。它还可以添上几样内建的数据结构——诸如列表与映射——并且它无疑还需要一份用于文件 I/O、用户输入等操作的核心库。但语言本身已经够用了。我们已然拥有了一门小巧的过程式语言，与 BASIC、Tcl、Scheme（去掉宏的部分）、以及早期版本的 Python 和 Lua 属于同宗。

若这是八十年代，我们便就此打住了。但放眼今天，许多流行的语言都支持"面向对象编程"。为 Lox 引入这一点，将为用户奉上一套他们耳熟能详的工具，用以编写更大的程序。即便你个人并<span name="hate">不钟爱</span>OOP，本章与[下一章][inheritance]仍将助你理解他人是如何设计与构建对象系统的。

[inheritance]: inheritance.html

<aside name="hate">

不过，若你**当真**反感类，大可跳过这两章。它们与本书的其余部分相当独立。说来有趣的是，我个人倒是觉得多去了解那些自己不喜欢的事物是一件好事。远观时事物看似简单，但当真走近，细节便会浮现而出，而你便会获得一份更为细腻的认知。

</aside>

## OOP 与类

通往面向对象编程的道路大抵有三条：类、[原型][prototypes]、以及<span name="multimethods">[多重分派][multimethods]</span>。类最先出现，也是最为流行的风格。伴随着 JavaScript 的崛起（以及在较小范围内的 [Lua][]），原型也变得比以往更广为人知。关于原型，我会在[稍后][later]再谈。就 Lox 而言，我们——咳咳——采取了经典路线。

[prototypes]: http://gameprogrammingpatterns.com/prototype.html
[multimethods]: https://en.wikipedia.org/wiki/Multiple_dispatch
[lua]: https://www.lua.org/pil/13.4.1.html
[later]: #design-note

<aside name="multimethods">

多重分派大概是你最不熟悉的一种。我很乐意再多聊几句——我曾围绕它设计过[一门业余爱好语言][magpie]，那种体验**简直妙不可言** ——但本书的篇幅毕竟有限。若你意欲了解更多，不妨看看 [CLOS][]（Common Lisp 中的对象系统）、[Dylan][]、[Julia][]，或 [Raku][]。

[clos]: https://en.wikipedia.org/wiki/Common_Lisp_Object_System
[magpie]: http://magpie-lang.org/
[dylan]: https://opendylan.org/
[julia]: https://julialang.org/
[raku]: https://docs.raku.org/language/functions#Multi-dispatch

</aside>

既然你已与我共同书写了大约一千行 Java 代码，我便假定你不必再需要一份关于面向对象的详尽介绍。其主要目的在于将数据与作用于其上的代码捆绑在一起。用户通过声明**类**来达成此目的，而类则：

<span name="circle"></span>

1. 暴露一个**构造器**，用以创建并初始化该类的新**实例**；

1. 提供一种方式来存储并访问实例上的**字段**；

1. 定义一组被该类所有实例所共享的**方法**，这些方法将作用于各自实例的状态之上。

这已经是最精简的版本了。大多数面向对象的语言——一路追溯到 Simula——还提供继承机制，以便跨类复用行为。我们将在[下一章][inheritance]中加入这一点。即便将继承排除在外，我们仍旧有许多事情要做。这一章内容很长，而所有这些零碎的部分要凑在一起才能完全成形——所以，请攒足你的耐力。

<aside name="circle">

<img src="image/classes/circle.png" alt="类、方法、实例、构造器、字段之间的关系图。" />

这就像生命的轮回，只是少了 Elton John 爵士。

</aside>

[inheritance]: inheritance.html

## 类声明

如同以往，我们从语法入手。一条 `class` 语句引入了一个新名字，因此它归属于 `declaration` 文法规则。

```ebnf
declaration    → classDecl
               | funDecl
               | varDecl
               | statement ;

classDecl      → "class" IDENTIFIER "{" function* "}" ;
```

这条新的 `classDecl` 规则倚赖于我们先前所定义的 `function` 规则。为唤起回忆：

[function rule]: functions.html#function-declarations

```ebnf
function       → IDENTIFIER "(" parameters? ")" block ;
parameters     → IDENTIFIER ( "," IDENTIFIER )* ;
```

简而言之，一个类声明由 `class` 关键字、类的名字、以及一对花括号包裹的类体构成。类体内部是一系列方法声明。不同于函数声明，方法并不带一个前置的 <span name="fun">`fun`</span> 关键字。每一个方法都是一个名字、一个参数列表、以及一个函数体。示例如下：

<aside name="fun">

我并不是要说方法就不好玩了。

</aside>

```lox
class Breakfast {
  cook() {
    print "Eggs a-fryin'!";
  }

  serve(who) {
    print "Enjoy your breakfast, " + who + ".";
  }
}
```

与大多数动态类型语言一样，字段并不会在类声明中显式罗列。实例乃是数据的松散集合，你可以按自己的喜好，用普通的命令式代码自由地往里增添字段。

在我们这边的 AST 生成器中，`classDecl` 文法规则拥有它自己的语句<span name="class-ast">节点</span>。

^code class-ast (1 before, 1 after)

<aside name="class-ast">

新节点的生成代码收录于[附录 II][appendix-class]。

[appendix-class]: appendix-ii.html#class-statement

</aside>

它存储了类的名字及其类体中的方法。方法由现有的 `Stmt.Function` 类加以表示——那是我们用于函数声明 AST 节点的类。如此一来，我们便拥有了表示一个方法所需的全部状态：名字、参数列表、以及函数体。

类可以出现在任何允许具名声明出现的位置，并由那个前置的 `class` 关键字加以触发。

^code match-class (1 before, 1 after)

它转而调用：

^code parse-class-declaration

相比其它大多数解析方法，这一处的内容更为丰盈，但大体上仍紧贴文法。我们已经消耗掉了 `class` 关键字，因此接下来便去寻找那个所期待出现的类名，再接着是作为开头的花括号。一旦进入类体内部，我们便反复解析方法声明，直至撞上作为结尾的花括号。每一份方法声明都由一次对 `function()` 的调用进行解析——该函数定义于我们[介绍函数的那一章][functions]。

[functions]: functions.html

正如我们在语法分析器中任何一处开放式循环里所做的那样，我们同样会去检查是否撞上了文件末尾。这种情况在正确的代码中不会发生，因为一个类理应以一个作为结尾的花括号收尾；但它能确保语法分析器**不会**在用户犯了语法错误、忘记正确地结束类体时，被卡在一个死循环之中。

我们将类名与方法列表打包进一个 `Stmt.Class` 节点，便大功告成。此前，我们都是直接跳入解释器；但现在我们需要先让这个节点流过解析器。

^code resolver-visit-class

我们眼下并不需要操心对方法本身的解析工作，所以现在我们只需要以其名字**声明**该类即可。在局部变量中声明类并不常见，但 Lox 允许这么做，因此我们需要正确地处理它。

现在我们来解释类声明。

^code interpreter-visit-class

这与执行函数声明的方式颇为相似。我们在当前环境中声明该类的名字。随后，我们将类**语法节点**转换为一个 `LoxClass`，即类的**运行时**表示。我们回过头来，将类对象存放在我们先前声明的那个变量之中。这种两阶段的变量绑定过程，允许我们在类自己的方法内部引用类自身。

我们在本章中会不断打磨它，但 `LoxClass` 的初版大致是这样的：

^code lox-class

字面上看，它只是一个名字的外壳。眼下我们甚至尚未存储方法。这一点儿也不实用，但至少它带有一个 `toString()` 方法，使得我们能写一段简陋的脚本来测试类的对象确实正在被解析与执行。

```lox
class DevonshireCream {
  serveOn() {
    return "Scones";
  }
}

print DevonshireCream; // 打印 "DevonshireCream"。
```

## 创建实例

我们已有了类，但它们眼下还无所事事。Lox 没有"静态"方法——即可以直接在类对象本身调用的方法——所以没有真正的实例，类便毫无用处。因此，下一步便是实例。

虽然某些语法与语义在面向对象语言之间相当标准化，但创建新实例的方式却各有不同。Ruby 沿袭 Smalltalk 的做法，通过在类对象自身上调用一个方法来创建实例——这是一种<span name="turtles">递归式</span>优雅的途径。某些语言——比如 C++ 与 Java——则拥有一枚专门用于诞生新对象的 `new` 关键字。Python 则让你像调用一个函数那般"调用"类本身。（总是与众不同 JavaScript，则两者皆有几分。）

<aside name="turtles">

在 Smalltalk 中，甚至连**类**自身也是通过对一个既有对象（通常是其所需的父类）调用方法而来。这是一种"乌龟一路背到天"的哲学。它最终落在几块运行时就**凭空**召唤出来的魔法类上——比如 Object 与 Metaclass。

</aside>

我对 Lox 采用了极简主义路线。我们已有类对象，亦有函数调用，因此我们将借助对类对象的调用表达式来创建新实例。就好像类乃是一座能自我复制的工厂函数。这对我来说颇为优雅，也免得我们引入诸如 `new` 之类的语法。因此，我们可以径直穿过前端，直抵运行时。

眼下，若你尝试下面这段：

```lox
class Bagel {}
Bagel();
```

你会收到一个运行时错误。`visitCallExpr()` 会检查被调用对象是否实现了 `LoxCallable` 接口，由于 LoxClass **尚未**实现该接口，它便会报告一个错误。但尚未实现而已。

^code lox-class-callable (2 before, 1 after)

实现该接口要求两个方法。

^code lox-class-call-arity

真正有趣的是 `call()`。当你"调用"一个类时，它会为那个被调用的类实例化一份新的 `LoxInstance` 并将其返回。`arity()` 方法是解释器用来核验你传给 callable 的实参数量是否正确的途径。眼下，我们规定**不能**传入任何实参。等到我们引入用户自定义的构造器时，我们再回头修订这一限制。

由此便引出了 `LoxInstance`——Lox 中一个实例的运行时表示。同样地，我们的初版实现保持小巧。

^code lox-instance

与 `LoxClass` 一样，它目前还相当简陋，但我们才刚刚起步。若你想试一试，可以跑跑下面这段脚本：

```lox
class Bagel {}
var bagel = Bagel();
print bagel; // 打印 "Bagel instance"。
```

这段程序尚无太多作为，但它已开始做**一些**事情了。

## 实例上的属性

我们已有实例，接下来该让它们有用武之地了。我们正站在一处岔路口。我们可以先添加行为——方法——也可以先着手状态——属性。我们将选择后者，因为正如你将看到的，这两者将以一种有趣的方式纠缠在一起，而若先把属性跑通，再去理解它们则会容易得多。

Lox 在如何处理状态这一问题上，效仿 JavaScript 与 Python。每一个实例都是一组命名值的开放集合。实例所属类上的方法能够访问并修改这些属性，但<span name="outside">外部</span>的代码同样可以。属性通过 `.` 语法加以访问。

<aside name="outside">

允许类之外的代码直接修改对象的字段，这与面向对象信条中"类**封装**状态"的理念背道而驰。一些语言采取了更为坚定的立场。在 Smalltalk 中，字段通过简单的标识符访问——本质上，它们只是仅在类的方法内部处于作用域的变量。Ruby 使用 `@` 后跟一个名字来访问对象中的字段。这种语法仅在方法内部才有意义，且始终访问当前对象上的状态。

Lox，无论好坏，对它 OOP 信仰的虔诚度并不那么高。

</aside>

```lox
someObject.someProperty
```

一个表达式后跟一个 `.` 与一个标识符，即从该表达式所求值到的那个对象中读取那个名字的属性。这个点号与函数调用表达式中那对括号具有相同的优先级，因此我们通过用以下的规则替换既有的 `call` 规则来将其嵌进文法：

```ebnf
call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
```

在一级表达式之后，我们允许任意混合的括号调用与点号属性访问这两种语法形式。"属性访问"念起来颇为拗口，因此从现在起，我们将其简称为"get 表达式"。

### get 表达式

<span name="get-ast">语法树节点</span>长这样：

^code get-ast (1 before, 1 after)

<aside name="get-ast">

新节点的生成代码收录于[附录 II][appendix-get]。

[appendix-get]: appendix-ii.html#get-expression

</aside>

依照文法，新的解析代码被安插于我们既有的 `call()` 方法之中。

^code parse-property (3 before, 4 after)

外层的那个 `while` 循环对应于文法规则中的 `*`。我们沿着词法单元一路前行，每当遇到括号或点号，便构建出一条由调用与 get 相互串联的链条，过程如下图：

<img src="image/classes/zip.png" alt="解析一连串 '.' 与 '()' 表达式为 AST 的过程。" />

新 `Expr.Get` 节点的实例会被送入解析器之中。

^code resolver-visit-get

好的，这部分没什么可说的。因为属性是<span name="dispatch">动态地</span>查找的，它们并不参与解析。在解析过程中，我们仅仅递归地进入点号左侧的那个表达式。真正的属性访问发生在解释器中。

<aside name="dispatch">

你其实可以**直接**看出 Lox 中的属性分派是**动态的**，因为我们**并不**在静态解析 pass 中处理属性名。

</aside>

^code interpreter-visit-get

首先，我们对那个其属性正在被访问的表达式进行求值。在 Lox 中，只有类的实例才拥有属性。倘若该对象是某种其它类型——例如一个数字——那么对它发起一次 getter 操作便是一个运行时错误。

倘若该对象是一个 `LoxInstance`，那么我们便会让它去查找该属性。看来是时候给 `LoxInstance` 一些真实的状态了。一张 Map 足矣。

^code lox-instance-fields (1 before, 2 after)

Map 中的每一个键皆是一个属性名，与之对应的值便是该属性的值。要在一个实例上查找一个属性：

^code lox-instance-get-property

<aside name="hidden">

对每一次字段访问都做一次哈希表查找，对于许多语言实现而言已然足够快，但并非上乘之选。JavaScript 之类语言的高性能 VM 会使用诸如"[隐藏类][hidden classes]"这样的复杂优化手段来规避这一开销。

颇具反讽意味的是，许多为**动态**语言发明的速度优化手段，却建立在这样一项观察之上——即便在这些语言中，大多数代码在**所操作的对象的类型以及它们的字段**方面，仍然相当静态。

[hidden classes]: http://richardartoul.github.io/jekyll/update/2015/04/26/hidden-classes.html

</aside>

我们需要处理的一个饶有趣味的边角情形是：当实例**并不**拥有那个指定名字的属性时，会发生什么。我们本可以默默地返回一个 `nil` 之类的哑值，但根据我在 JavaScript 等语言上的经验，这种行为比起其它任何用途，都更容易掩盖 bug。取而代之，我们让它成为一个运行时错误。

因此，我们首先要做的是检查该实例是否真的拥有给定名字的字段。只有当它确实拥有时，我们才将其返回。否则，我们便抛出一个错误。

请注意，我是如何从谈论"属性"切换到"字段"的。两者之间存在着一处细微的差别。字段乃是直接存储于实例中的命名状态。属性则是 get 表达式可能返回的那个命名**东西**。每一个字段都是一个属性，但正如我们<span name="foreshadowing">稍后</span>将看到的，并非每一个属性都是一个字段。

<aside name="foreshadowing">

哦，伏笔。阴森森的。

</aside>

理论上，我们**现在**终于能够读取对象上的属性了。但由于尚无任何办法真正将状态塞进一个实例之中，因此根本没有字段可供访问。在我们能够测试读取之前，我们必须先支持写入。

### set 表达式

setter 使用与 getter 相同的语法，只不过它们出现在赋值表达式的左侧。

```lox
someObject.someProperty = value;
```

在文法的世界里，我们将 assignment 规则扩展为允许在左侧出现以点号连接的标识符。

```ebnf
assignment     → ( call "." )? IDENTIFIER "=" assignment
               | logic_or ;
```

与 getter 不同，setter 并不串联。然而，规则中对 `call` 的引用，允许在最后一个点号之前出现任意高优先级的表达式，其中包括任意数量的 *getter*，例如：

<img src="image/classes/setter.png" alt="breakfast.omelette.filling.meat = ham" />

请注意，此处**只有**最后一部分——即 `.meat` 那部分——是**setter**。`.omelette` 与 `.filling` 两部分都是**get**表达式。

正如我们对变量访问与变量赋值各自拥有独立的 AST 节点一样，我们也需要一个<span name="set-ast">独立的 setter 节点</span>，与我们先前的 getter 节点相互呼应。

^code set-ast (1 before, 1 after)

<aside name="set-ast">

新节点的生成代码收录于[附录 II][appendix-set]。

[appendix-set]: appendix-ii.html#set-expression

</aside>

万一你已然忘了，对于赋值，我们语法分析器的处理方式多少有些奇特。我们无法轻易判断一连串词法单元是赋值的左侧，直至我们撞上那个 `=`。如今——既然我们的赋值文法规则的左侧有了 `call`，它可以扩展为任意庞大的表达式——那个作为结尾的 `=` 可能会出现在与我们需要知道"我们正在解析一个赋值"的位置相距许多个词法单元之处。

取而代之，我们所使用的招数是：把左侧当作一个普通表达式来解析。待我们随后撞上那道等号之后，我们再去取那份已然解析好的表达式，并将其变形为赋值的正确语法树节点。

我们向那一变形过程中再添加一条分支，用以将一条位于左侧的 `Expr.Get` 表达式转化为对应的 `Expr.Set`。

^code assign-set (1 before, 1 after)

至此完成了语法解析。我们将那个节点向下推入解析器。

^code resolver-visit-set

同样地，与 `Expr.Get` 一样，属性本身是动态求值的，因此那里没有什么需要解析的。我们所需要做的，仅仅是递归地进入 `Expr.Set` 的两个子表达式——那个其属性正在被设置的对象，以及那个被设置的值。

这便把我们带到了解释器。

^code interpreter-visit-set

我们对那个其属性正在被设置的对象进行求值，并检查它是否是一个 `LoxInstance`。若不是，那便是一个运行时错误。否则，我们对那个被设置的值进行求值，并将其存储到实例之上。这有赖于 `LoxInstance` 中新增的一个方法。

<aside name="order">

这又是另一个语义上的边角情形。一共存在三个截然不同的操作：

1.  对该对象进行求值。

2.  若它并非一个类的实例，则抛出一个运行时错误。

3.  对该值进行求值。

这三者的执行顺序对用户而言可能可见，这意味着我们需要仔细地明确它，并确保我们的实现都以相同的顺序执行它们。

</aside>

^code lox-instance-set-property

这其中并无任何真正的魔法。我们直接将那些值塞进 Java 的 Map——字段所栖身之处。既然 Lox 允许在实例上自由地创建新字段，便无需先去查看该键是否已然存在。

## 类上的方法

你可以在类上创建实例并往里塞数据，但类本身**实质上**还没有**做**任何事情。实例仅仅是一张 Map，所有的实例大致都是相同的。要让它们感觉是**某**一类的实例，我们需要行为——方法。

我们那位勤勉的语法分析器已然在做方法声明的解析工作，所以这一步我们无需多虑。我们也**不**需要为方法**调用**添加任何新的语法支持。我们已经拥有了 `.`（getter）与 `()`（函数调用）。所谓"方法调用"只不过是将这两者串联起来。

<img src="image/classes/method.png" alt="'object.method(argument)' 的语法树" />

这便引出了一个有趣的问题。当那两个表达式被分开时，会发生什么？假设此处的 `method` 是 `object` 所属类上的一个方法，而非该实例上的一个字段，那么下面这段代码应当作何行为？

```lox
var m = object.method;
m(argument);
```

这段程序"查找"出了那个方法，并将结果——无论那是什么——存入一个变量中，稍后再去调用它。这样被允许吗？你能否如同对待实例上的一个函数那般，去对待一个方法？

那反过来呢？

```lox
class Box {}

fun notMethod(argument) {
  print "called function with " + argument;
}

var box = Box();
box.function = notMethod;
box.function("argument");
```

这段程序创建了一个实例，并将一个函数存入它的一个字段中。随后，它使用与一次方法调用相同的语法调用了该函数。这样能跑通吗？

不同的语言对于这些问题各有不同的答案。要写一篇专题论文都不为过。就 Lox 而言，我们且说这两种情况的答案都是**能**。我们有几条理由来支持这一决定。对于第二个例子——即调用一个存储在字段中的函数——我们希望支持它，因为一等函数本就很有用，而将它们存储在字段中也完全是件稀松平常的事。

第一个例子则更为冷门。一种动机是用户通常期望能够将一个子表达式提取到一个局部变量之中，而**不**改变程序的语义。你可以这样写：

```lox
breakfast(omelette.filledWith(cheese), sausage);
```

然后改成这样：

```lox
var eggs = omelette.filledWith(cheese);
breakfast(eggs, sausage);
```

两者做的是同一件事。类似地，由于方法调用中的 `.` 与 `()` 原本就是两个相互独立的表达式，似乎理应能够将那个**查找**步骤提取到一个变量里，然后稍后再去**调用**它<span name="callback">。</span>我们需要仔细思索一下，当你查找一个方法时所**得到**的究竟**是**什么东西，以及它**如何**行为——即便是在下面这样诡异的情况下：

<aside name="callback">

这种用法的一个有动机的用例是回调。你常常希望传递一个回调，其函数体仅仅是在某个对象上调用一个方法。能够直接查找该方法并将其原样传入，便可省去手动声明一个函数以包裹它的麻烦。请对比下面这两种写法：

```lox
fun callback(a, b, c) {
  object.method(a, b, c);
}

takeCallback(callback);
```

与：

```lox
takeCallback(object.method);
```

</aside>

```lox
class Person {
  sayName() {
    print this.name;
  }
}

var jane = Person();
jane.name = "Jane";

var method = jane.sayName;
method(); // ？
```

如果你获取了某个实例上的一个方法的句柄，并在稍后调用它，那么它会"记得"当初它是从哪个实例上取下来的吗？方法中的 `this` 仍会指向那个原始的对象吗？

这里有一道更令人费解的例子来折磨你的脑子：

```lox
class Person {
  sayName() {
    print this.name;
  }
}

var jane = Person();
jane.name = "Jane";

var bill = Person();
bill.name = "Bill";

bill.sayName = jane.sayName;
bill.sayName(); // ？
```

这最后一行究竟会打印 "Bill"——因为那是我们**调用**方法所穿过的那个实例——还是 "Jane"——因为它是我们最初抓取方法的源头？

Lua 与 JavaScript 中的等价代码会打印 "Bill"。这些语言**其实**并没有真正意义上的"方法"概念。一切都多少像是"字段里装着的函数"，因此"jane 比 bill 更加**拥有** `sayName`"这一说法并不明确。

Lox 则拥有货真价实的类语法，因此我们确实**知道**哪些可调用之物是方法、哪些是函数。因此，与 Python、C# 以及其它一些语言一样，我们将让方法在**首次**被抓取时便将 `this` **绑定**到那个原始的实例。Python 称之为<span name="bound">**绑定方法**</span>。

<aside name="bound">

我知道，这名字可真够富于想象力的，对吧？

</aside>

在实践中，这通常正是你想要的。倘若你在某个对象上抓取一个方法的引用，以便日后将其作为回调使用，你自然希望它**记住**那个原本所属的实例，即便那个回调碰巧被存放在了**另一个**对象的字段里。

好了，这一番语义上的重头戏就这样塞进了你的脑子里。暂时把那些边角情形放到一边。我们稍后再回过头去处理它们。现在，让我们先把基本的方法调用跑通。方法声明已经在类体的解析中处理完毕了，所以下一步便是对它们进行解析。

^code resolve-methods (1 before, 1 after)

<aside name="local">

将函数类型存于一个局部变量之中眼下有些多余，但过不了多久我们便会扩展这段代码，届时它的意义便会显现。

</aside>

我们遍历类体中的方法，并调用我们先前为处理函数声明而写就的 `resolveFunction()` 方法。唯一的不同之处在于，我们传入一个新的 `FunctionType` 枚举值。

^code function-type-method (1 before, 1 after)

当我们解析 `this` 表达式时，这一点会变得重要起来。眼下，先别担心它。真正有趣的内容在解释器之中。

^code interpret-methods (1 before, 1 after)

当我们解释一条类声明语句时，我们便将类的语法表示——其 AST 节点——转换为它的运行时表示。现在，我们还需要对类中所包含的各个方法做同样的事。每一份方法声明都绽放为一枚 `LoxFunction` 对象。

我们将它们全部收入一张 Map，以方法名作为键。这张 Map 会被存储于 `LoxClass` 之中。

^code lox-class-methods (1 before, 3 after)

实例用于存储状态，而类用于存储行为。`LoxInstance` 拥有一张它的字段 Map，而 `LoxClass` 则拥有一张它的方法 Map。尽管方法为类所"拥有"，它们依然需要通过该类的实例来访问。

^code lox-instance-get-method (5 before, 2 after)

当在一个实例上查找一个属性时，若我们**没有**找到匹配的字段，我们便去其所属类上寻找同名方法。若找到了，我们便将其返回。正是在这里，"字段"与"属性"之间的区分才真正具有意义。当访问一个属性时，你可能拿到一个字段——一小块存储于实例之上的状态——亦可能命中定义于该实例所属类上的一个方法。

该方法是通过下面这一函数查找到的：

<aside name="shadow">

先查找字段意味着字段会遮蔽方法——这是一个微妙却重要的语义细节。

</aside>

^code lox-class-find-method

你大概能猜到，这个方法日后会变得更为有趣。眼下，简单地在类的方法表上做一次 Map 查找，便足以让我们起步。试试看：

<span name="crunch"></span>

```lox
class Bacon {
  eat() {
    print "Crunch crunch crunch!";
  }
}

Bacon().eat(); // 打印 "Crunch crunch crunch!"。
```

<aside name="crunch">

若你偏爱嚼劲的培根而非酥脆的那种，敬请调整脚本以贴合你的口味。

</aside>

## this

我们既能在对象上定义行为，又能存储状态，但它们**尚未**关联到一起。在一个方法内部，我们既无法访问"当前"对象——也就是那个方法被调用时所**针对**的实例——的字段，也无法在同一对象上调用其它方法。

为了访问那个实例，它需要一个<span name="i">名字</span>。Smalltalk、Ruby 与 Swift 使用 "self"。Simula、C++、Java 以及其它一些语言使用 "this"。Python 约定俗成地使用 "self"，但技术上你也可以随你喜好给它起个别的名字。

<aside name="i">

"I" 倒是个绝佳选择，但将 "i" 用作循环变量这一惯例早在 OOP 出现之前便已存在，它一路可以追溯到 Fortran。我们都是前辈们那些偶然选择之下的受害者。

</aside>

就 Lox 而言，由于我们大体上沿袭 Java 风格，因此我们也选用 "this"。在一个方法体内部，一个 `this` 表达式会求值为那个方法被调用时所**针对**的实例。或者，更准确地说——由于方法先是**被访问**，然后再被**调用**这两个步骤——它所指的将是那个方法**被访问时**所**针对**的对象。

这让我们的工作变得更为棘手。请看一眼：

```lox
class Egotist {
  speak() {
    print this;
  }
}

var method = Egotist().speak;
method();
```

在倒数第二行，我们从某个类的一个实例上抓取了对 `speak()` 方法的引用。那会返回一个函数，而那个函数需要记住它**是从**哪个实例上取下来的，以便**日后** ——在最后一行——当该函数被调用时，它依然能在其中找到它。

我们需要在方法被访问的那一时刻便取下 `this`，并以某种方式将其与该函数绑定在一起，以使它在我们需要它的时间里始终存在。嗯……一种用来存放那些伴随函数而存在的额外数据的方法？这听起来**是不是**有点像一个**闭包**？

如果我们把 `this` 定义为一个隐藏的变量，存在于一个包裹着"当我们查找一个方法时所返回的那个函数"的环境之中，那么方法体中对 `this` 的引用便能在日后找到它。`LoxFunction` 已经具备了抓住一份外层环境的能力，因此我们手头已然拥有所需的工具。

让我们通过一个例子走一遍，看看它究竟是如何工作的：

```lox
class Cake {
  taste() {
    var adjective = "delicious";
    print "The " + this.flavor + " cake is " + adjective + "!";
  }
}

var cake = Cake();
cake.flavor = "German chocolate";
cake.taste(); // 打印 "The German chocolate cake is delicious!"。
```

当我们首次对类定义进行求值时，我们为 `taste()` 创建了一枚 `LoxFunction`。它的闭包是包裹该类的那份环境，于此例中便是全局环境。因此，我们存放在类方法 Map 中的那枚 `LoxFunction`，其形如下：

<img src="image/classes/closure.png" alt="该方法最初的闭包。" />

当我们对那条 `cake.taste` 的 get 表达式进行求值时，我们创建了一份新的环境，它将 `this` 绑定到那个方法被访问时所针对的对象（在此处为 `cake`）。随后，我们用一份新的 `LoxFunction` 来承载同一段代码，但将那份新的环境作为它的闭包。

<img src="image/classes/bound-method.png" alt="绑定了 'this' 的新闭包。" />

这便是当对方法名的 get 表达式进行求值时所返回的那枚 `LoxFunction`。当那枚函数稍后被一条 `()` 表达式所调用时，我们照例为方法体创建一份新的环境。

<img src="image/classes/call.png" alt="调用绑定方法并为方法体创建一份新环境。" />

那方法体环境的父环境，正是我们先前所创建的那份用于将 `this` 绑定到当前对象的环境。于是，在方法体中对 `this` 的任何一次使用，都能够顺利地解析到那个实例。

复用我们既有的环境代码来实现 `this`，同时也妥善处理了方法与函数彼此交互的一些有趣情形，例如：

```lox
class Thing {
  getCallback() {
    fun localFunction() {
      print this;
    }

    return localFunction;
  }
}

var callback = Thing().getCallback();
callback();
```

比如说在 JavaScript 中，从一个方法内部返回一个回调是件寻常事。那个回调或许希望**抓住**并保留对那个原始对象——那个方法原本所关联的 `this` 值——的访问。我们对闭包与环境链的既有支持理应能正确地处理这一切。

让我们来动手实现它。第一步是为 `this` 新增<span name="this-ast">语法</span>。

^code this-ast (1 before, 1 after)

<aside name="this-ast">

新节点的生成代码收录于[附录 II][appendix-this]。

[appendix-this]: appendix-xi.html#this-expression

</aside>

由于它只是一个单一词法单元，而我们的词法分析器早已将其识别为保留字，解析这一步简单得很。

^code parse-this (2 before, 2 after)

待到解析器之中，你便能开始看到 `this` 工作起来有多像一个变量。

^code resolver-visit-this

我们将以字符串 "this" 作为"变量"的名字，仿照其它任何局部变量那般解析它。当然，眼下这么做还**不行**，因为 "this" 并没有在任何作用域中被声明。我们这就到 `visitClassStmt()` 中去补上它。

^code resolver-begin-this-scope (2 before, 1 after)

在我们踏入并开始解析方法体之前，我们推入一个新的作用域，并将 "this" 定义于其中，仿佛它是一个变量。而当我们搞定之后，我们便丢弃掉那份外层的作用域。

^code resolver-end-this-scope (2 before, 1 after)

如今，每当遇上 `this` 表达式（至少在方法内部）时，它都会解析为一个定义于方法体的花括号**之外**那一处隐式作用域中的"局部变量"。

解析器为 `this` 引入了一个新的**作用域**，因此解释器也需要为之创建一份对应的**环境**。记住，我们必须始终保持解析器的作用域链与解释器的链接环境彼此同步。在运行时，我们在从实例上找到方法之后才创建那份环境。我们将之前那条仅返回方法 `LoxFunction` 的代码替换为如下：

^code lox-instance-bind-method (1 before, 3 after)

请注意新增的那次 `bind()` 调用。它的实现如下：

^code bind-instance

内容并不多。我们创建了一份新的环境，嵌于该方法原有的闭包之内。可以视为"闭包中的闭包"。当该方法被调用时，这将成为方法体环境的父环境。

我们将 "this" 声明为该环境中的一个变量，并将其绑定到给定的实例——即那个方法**被访问时**所**针对**的实例。**Voilà**，所返回的 `LoxFunction` 如今便随身携带着它自己那一小片持久化的天地，其中 "this" 已被绑定到那个对象。

剩下的任务便是解释那些 `this` 表达式。与解析器类似，这完全同于解释一个变量表达式。

^code interpreter-visit-this
去试试吧，用一下前面那个 `cake` 的例子。区区不到二十行代码，我们的解释器便能在方法内部处理 `this`——包括它与嵌套类、方法内部的函数、方法的句柄等等之间所有**诡异**的交互。

### this 的无效使用

且慢。倘若你试图在方法**之外**使用 `this`，会怎样？比如：

```lox
print this;
```

或者：

```lox
fun notAMethod() {
  print this;
}
```

既然你并不身处一个方法之中，那么 `this` 便无所指代。我们可以给它一个 `nil` 之类的默认值，或将其作为一个运行时错误；但用户显然已经犯了一个错。越早令他们察觉并修补此错，他们便越开心。

我们的解析 pass 是检测这一错误的绝佳之处。它早已能够检测函数外的 `return` 语句。我们对 `this` 也照此办理。沿袭我们已有的 `FunctionType` 枚举的思路，我们新定义一个 `ClassType`。

^code class-type (1 before, 1 after)

是的，它本可以是一个布尔值。等我们讲到继承时，它会添上第三种取值，正因如此，我们才在此先以枚举的形式出现。我们还顺带添加一个与之对应的字段 `currentClass`。它的取值会告诉我们，在遍历语法树的过程中，我们是否正身处某条类声明之中。最初它为 `NONE`，意味着我们并不身处其中。

当我们开始解析一条类声明时，便改变该字段。

^code set-current-class (1 before, 1 after)

如同 `currentFunction` 那样，我们先将字段的旧值存放于一个局部变量之中。这让我们得以借力于 JVM 自身来维护一座 `currentClass` 值的栈——如此一来，即便一个类嵌套于另一个类之中，我们也不会丢失对先前值的追踪。

待类中的方法解析完毕之后，我们便通过恢复旧值来"弹出"那座栈。

^code restore-current-class (2 before, 1 after)

当我们解析 `this` 表达式时，`currentClass` 字段会给我们提供所需的这份数据——以报告当该表达式**不是**出现在某个方法体内部时出现的错误。

^code this-outside-of-class (1 before, 1 after)

这应当能帮助用户正确地使用 `this`，并省去我们在解释器中处理运行时误用的麻烦。

## 构造器与初始化器

时至今日，类上几乎所有的功能都已就绪，而当我们行至本章的尾声时，我们发现自己竟奇怪地聚焦于一个"开始"。方法与字段让我们能将状态与行为封装在一起，从而保证一个对象始终**保持**在一种合法的状态之中。但我们如何保证一个全新的对象**起始**便处于一种良好的状态呢？

为此，我们需要构造器。我觉得它们是语言设计中最棘手的部分之一，若你仔细端详大多数其它语言，你会发现那些围绕"对象构造"所留下的<span name="cracks">裂痕</span>——设计的接缝处总是难以严丝合缝。或许，在"诞生"的那一时刻，某些本质性的混乱便是躲不掉的。

<aside name="cracks">

几个例子：在 Java 中，即便 `final` 字段必须被初始化，但依然可能在它们被赋值**之前**读取它们。异常——一项庞大而复杂的特性——被加入到 C++ 中，主要便是作为一种从构造器中发出错误的方式。

</aside>

"构造"一个对象事实上是一对操作：

1.  运行时为一份崭新的实例<span name="allocate">**分配**</span>其所需的内存。在大多数语言中，这项操作处于用户代码所能触及的层面**之下**。

    <aside name="allocate">

    C++ 的"[placement new][]"是少数几个将分配的肠肚裸露出来供程序员戳弄的例子之一。

    </aside>

2.  随后，一段由用户提供的代码段被调用，对那份尚未成形的对象进行**初始化**。

[placement new]: https://en.wikipedia.org/wiki/Placement_syntax

后者便是我们听到"构造器"一词时通常会想到的那个东西，但语言本身在我们抵达那一步之前往往已经替我们做好了铺垫。事实上，我们的 Lox 解释器在创建一份新的 `LoxInstance` 对象时便已经完成了这部分工作。

我们现在要来兑现剩下的部分——用户自定义的初始化。语言为那段"为一个新对象做好铺垫"的代码提供了多种多样的记法。C++、Java 与 C# 使用一个与类同名的方法。Ruby 与 Python 则称之为 `init()`。后者简短利落，我们便采用这种。

我们向 `LoxClass` 的 `LoxCallable` 实现中再添几行代码。

^code lox-class-call-initializer (2 before, 1 after)

当一个类被调用时，在 `LoxInstance` 创建之后，我们便会去查找一个名为 "init" 的方法。若我们找到了它，便立刻将其绑定并调用，如同一次普通的方法调用。实参列表会被原样转发。

那个实参列表意味着我们也需要稍稍调整一下一个类声明其元数的方式。

^code lox-initializer-arity (1 before, 1 after)

若存在一个初始化器，那么该方法的元数便决定了你必须在调用类**本身**时传入多少个实参。不过为了方便起见，我们**并不**强制要求一个类必须定义一个初始化器。若你没有初始化器，则元数依然为零。

大体上就是这样。由于我们在调用 `init()` 之前便已将 `this` 与之绑定，因此在 `init()` 体内部可以访问到 `this`。再加上传入给类的实参，这些便足以让你随心所欲地设置那个新实例了。

### 直接调用 init()

一如既往，探索这片新的语义疆域又会掀出几头诡异的怪物。考虑：

```lox
class Foo {
  init() {
    print this;
  }
}

var foo = Foo();
print foo.init();
```

你能通过直接调用其 `init()` 方法来"重新初始化"一个对象吗？若你这么做了，它会返回什么？一个<span name="compromise">合理的</span>答案会是 `nil`——因为看上去函数体所返回的便是 `nil`。

然而——我向来不太喜欢为了迁就实现而妥协——倘若我们宣称 `init()` 方法**总是**返回 `this`（即便它是被直接调用的），那么 clox 中构造器的实现便会容易得多。为了让 jlox 与之兼容，我们在 `LoxFunction` 中加入了一小段特殊情形代码。

<aside name="compromise">

或许"不喜欢"这个词用得太过强烈了。让实现的种种约束与资源影响语言的设计，这本身是合理的。一天之中可用的时间就那么多，倘若在某处少走一条弯路便能让你更快地将更多特性交付到用户手中，那么这或许能使他们的愉悦与效率得到净收益。诀窍在于弄清**哪些**弯路可以走——而不会让你的用户以及未来的自己去咒骂你的短视。

</aside>

^code return-this (2 before, 1 after)

若该函数是一个初始化器，那么我们便覆写其实际的返回值，并强制令其返回 `this`。这有赖于一个新的 `isInitializer` 字段。

^code is-initializer-field (2 before, 2 after)

我们不能简单地通过查看 `LoxFunction` 的名字是否为 "init" 来判断，因为用户可以定义一个**函数**与之同名。在这种情况下，**便**没有 `this` 值得返回。为了避免**那种**诡异的边角情形，我们将直接存储该 `LoxFunction` 是否代表一个初始化器方法。这意味着我们需要回过头去修一修那些创建 `LoxFunction` 的地方。

^code construct-function (1 before, 1 after)

对于真正的函数声明，`isInitializer` 始终为 `false`。对于方法，我们则去检查其名字。

^code interpreter-method-initializer (1 before, 1 after)

然后在 `bind()` 中——在我们创建那份将 `this` 绑定到某个方法的闭包之处——我们把原方法的值一并传过去。

^code lox-function-bind-with-initializer (1 before, 1 after)

### 从 init() 返回

我们**仍未**走出深山老林。我们一直假设用户编写的初始化器并不会显式地返回一个值，因为大多数构造器都不这么做。若用户尝试下面这样：

```lox
class Foo {
  init() {
    return "something else";
  }
}
```

这显然**不会**做出他们想要的事，因此我们不妨将其作为一道静态错误。回到解析器中，我们再向 `FunctionType` 中添加一种情形。

^code function-type-initializer (1 before, 1 after)

我们借被访问方法的名字来判断我们究竟是在解析一个初始化器与否。

^code resolver-initializer-type (1 before, 1 after)

当我们之后审视到一条 `return` 语句时，我们便去检查该字段，并使"从一个 `init()` 方法内部返回一个值"成为一种错误。

^code return-in-initializer (1 before, 1 after)

我们**仍然**尚未完事。我们静态地禁止从一个初始化器内部返回一个**值**，但你仍然可以使用一条空白的提前 `return`。

```lox
class Foo {
  init() {
    return;
  }
}
```

这有时其实挺有用，因此我们不愿完全封禁它。取而代之，它应当返回 `this` 而非 `nil`。这只需在 `LoxFunction` 中做一处小小的修补即可。

^code early-return-this (1 before, 1 after)

若我们身处一个初始化器之中并执行了一条 `return` 语句，那么我们便不再返回那个值（它永远会是 `nil`），而改为再次返回 `this`。

呼！这一长串任务一口气列下来确实可观，但我们的回报是，我们那款小小的解释器已然长出了一整片编程范式。类、方法、字段、`this`，以及构造器。我们这门蹒跚学步的语言，如今看起来已然相当成熟。

<div class="challenges">

## 挑战

1.  我们在实例上拥有方法，但还没有办法定义"静态"方法——即可以直接在类对象自身上调用的方法。请为它们添加支持。在方法之前使用 `class` 关键字来指示一个静态方法，它挂载在类对象之上。

    ```lox
    class Math {
      class square(n) {
        return n * n;
      }
    }

    print Math.square(3); // 打印 "9"。
    ```

    你可以随心所欲地解决它，但Smalltalk 与 Ruby 所采用的"[元类][metaclasses]"是一种尤为优雅的途径。*提示：让 LoxClass 继承自 LoxInstance，然后从那里出发。*

1.  大多数现代语言都支持"getter"与"setter"——类中那些看起来像字段读写、实则执行用户自定义代码的成员。请扩展 Lox 以支持 getter 方法。它们在声明时不带参数列表。getter 的函数体会在访问与该同名的属性时执行。

    ```lox
    class Circle {
      init(radius) {
        this.radius = radius;
      }

      area {
        return 3.141592653 * this.radius * this.radius;
      }
    }

    var circle = Circle(4);
    print circle.area; // 粗略地打印 "50.2655"。
    ```

1.  Python 与 JavaScript 允许你从方法外部自由地访问对象的字段。Ruby 与 Smalltalk 则封装实例状态。只有类上的方法能够访问原始字段，至于对外暴露哪些状态，则由类自己决定。大多数静态类型语言提供诸如 `private` 与 `public` 之类的修饰符，以便在每一个成员的基础上控制外部可访问的类成员。

    这些方法各自的取舍如何？一种语言为何可能偏好其中某一种？

[metaclasses]: https://en.wikipedia.org/wiki/Metaclass

</div>

<div class="design-note">

## 设计笔记：原型与威力

在本章中，我们引入了两种新的运行时实体——`LoxClass` 与 `LoxInstance`。前者用于存放对象的行为，后者用于存放状态。倘若你能够直接在某一份 `LoxInstance` 上定义方法，会怎样？那样的话，我们便根本不需要 `LoxClass`。`LoxInstance` 自身便会是一份定义对象行为与状态的完整包。

我们仍会希望有某种方式——不借助类——在多个实例之间复用行为。我们可以让一份 `LoxInstance` *直接* [*委托*][delegate]给另一份 `LoxInstance`，以复用其后者的字段与方法，多少有一点像继承的味道。

用户便可以将其程序建模为一片由对象组成的星座，其中某些对象彼此委托，以反映它们之间的共性。那些被当作委托目标的对象，便是代表"规范的"或"原型的"对象，供其他对象去精炼。其结果是一个更为简单的运行时，仅有 `LoxInstance` 这一个内部构件。

这种范式之所以被称作**[原型][proto]**，便是因为此故。它由 David Ungar 与 Randall Smith 在一门名为 [Self][] 的语言中发明。他们通过从 Smalltalk 出发，沿着上述思路反复推演，问自己：究竟能砍到多简？

原型曾长期停留在学术圈子的冷门处——的确有趣，也催生了不少研究，但并未对更广阔的程序设计世界有多大影响。直到 Brendan Eich 将原型硬塞进 JavaScript，而 JavaScript 又旋即席卷了整个世界。关于 JavaScript 中的原型，已有（海量）<span name="words">著作</span>面世。这究竟证明原型是天才还是令人困惑——抑或两者兼而有之——依然是一个悬而未决的问题。

<aside name="words">

其中也包括[你眼前这位的几篇][prototypes]。

</aside>

我无意在此对原型是否是一门语言的好主意发表意见。我曾既设计过原型的语言，也设计过[基于类][wren] 的语言，对两者的看法都颇为复杂。我想讨论的是**简洁性**在一门语言中所扮演的角色。

原型比类更简洁——语言实现者要写的代码更少，用户需要学习与理解的概念也更少。这是否就使其更佳？我们这群语言书呆子往往会过分崇拜极简主义。说实话，在我看来，简洁只是等式的一部分。我们真正想要赋予用户的是**威力**，我将其定义为：

```text
威力 = 广度 × 易用性 ÷ 复杂度
```

这些并非精确的数值度量。我在此用的是数学的比喻，而非真正的量化。

*   **广度**指的是语言允许你表达的事物的范围。C 语言具有相当广的广度——它既被用于操作系统，也为用户应用与游戏所青睐。诸如 AppleScript 与 Matlab 之类的领域特定语言，其广度则相对有限。

*   **易用性**是指让语言去做你想做的事情需要付出的努力。"可用性"或许也是另一个说法，只是它所背负的包袱超出了我此刻愿意引入的范围。"更高级"语言往往比"较低级"语言拥有更高的易用性。大多数语言都有其"纹理"，某些事情表达起来更为顺手，另一些则不然。

*   **复杂度**涵盖了语言本身的体量（包括其运行时、核心库、工具、生态系统等）。人们谈论一门语言规范有多少页、它拥有多少关键字。它衡量的是用户在一门语言中具备生产力之前，必须将自己的"湿件"装进多少东西。它是简洁的反义词。

[proto]: https://en.wikipedia.org/wiki/Prototype-based_programming

降低复杂度**确实**会提升威力。分母越小，结果便越大，因此我们对"简洁是好事"的直觉自有其道理。然而，在降低复杂度时，我们必须小心，不要因此牺牲广度或易用性，否则总体威力反而可能下降。倘若 Java 删去字符串，那么它会是一门**更**简洁的语言，但它在文本处理任务方面多半也会失灵，且用户搞定事情也不会那么顺手。

由此，这门手艺便在于找出那些**偶然的**复杂度——即那些无法通过提升语言的广度或易用性来证明自身分量的语言特性与交互。

若用户希望用"对象类别"来表达他们的程序，那么将类烘焙进语言便会提升这样做的易用性——但愿提升的幅度足以抵消因此而带来的复杂度。然而，若用户并非如此使用你的语言，那么将类一概留出也自无妨。

</div>

[delegate]: https://en.wikipedia.org/wiki/Prototype-based_programming#Delegation
[prototypes]: http://gameprogrammingpatterns.com/prototype.html
[self]: http://selflanguage.org/
[finch]: http://finch.stuffwithstuff.com/
[wren]: http://wren.io/
