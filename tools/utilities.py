kinds = ['attributes', 'language', 'library']
implementations = ['clang', 'gcc', 'msvc']
standards = [
    ('C++98', 199711),
    ('C++11', 201103),
    ('C++14', 201402),
    ('C++17', 201703),
    ('C++20', 202002),
    ('C++23', 202302),
    ('C++26', None),
]

library_prologue = """\
#include <version>

#ifndef __is_identifier
# define __is_identifier(x) 1
#endif
#ifndef __has_builtin
# define __has_builtin(x) 0
#endif
#ifndef __has_keyword
# define __has_keyword(x) 0
#endif
"""

def std_options(impl):
    stdoptions = []
    for std, __cplusplus in standards:
        if impl == 'msvc':
            if std in ['C++98', 'C++11', 'C++26']:
                continue
            if std == 'C++23':
                stdoptions.append((std, '-std:c++latest'))
            else:
                stdoptions.append((std, f'-std:{std.lower()}'))
        else:
            stdoptions.append((std, f'-std={std.lower()}'))
    return stdoptions

def get_options(item):
    opts = item.get('option', '').split()
    opts += [negate_option(opt) for opt in item.get('option', '').split()]
    opts += item.get('enabled-by', '').split()
    opts += item.get('disabled-by', '').split()
    return opts

def to_identifier(option):
    if option.startswith('/') and option.endswith('-'):
        option = 'HASOPT_NO' + option[:-1]
    else:
        option = 'HASOPT' + option
    option = option.replace('-', '_')
    option = option.replace('/', '_')
    option = option.replace(':', '_')
    assert option.isidentifier()
    return option

def nonpedantic_option():
    return 'NO_pedantic'

def negate_option(option):
    if option.startswith('-f'):
        assert not option.startswith('-fno-')
        return '-fno-' + option[2:]
    else:
        assert option.startswith('/')
        assert not option.endswith('-')
        return option + '-'

class TestsuiteGenerator:
    def __init__(self, kind, impl):
        assert kind in kinds
        assert impl in implementations
        self.depth = 0
        self.output = ''
        self.kind = kind
        self.impl = impl

    def writeln(self, output):
        self.output += output+'\n'

    def start_if(self, condition):
        space = ' ' * self.depth
        self.depth += 1
        self.writeln(f"#{space}if {condition}")

    def start_elif(self, condition):
        space = ' ' * (self.depth - 1)
        self.writeln(f"#{space}elif {condition}")

    def start_else(self):
        space = ' ' * (self.depth - 1)
        self.writeln(f"#{space}else")

    def endif(self):
        self.depth -= 1
        space = ' ' * self.depth
        self.writeln(f"#{space}endif")

    def test_expr(self, name):
        if self.kind == 'attributes':
            return f'__has_cpp_attribute({name})'
        else:
            return f'{name}'

    def generate_positive_test(self, name, value):
        space = ' ' * self.depth
        self.writeln(f"#{space}if {self.test_expr(name)} != {value}")
        self.writeln(f"#{space} error {self.test_expr(name)} is not equal to {value}")
        self.writeln(f"#{space}endif")

    def generate_negative_test(self, name):
        space = ' ' * self.depth
        if self.kind == 'attributes':
            self.writeln(f"#{space}if __has_cpp_attribute({name})")
            self.writeln(f"#{space} error __has_cpp_attribute({name}) is nonzero")
            self.writeln(f"#{space}endif")
        else:
            self.writeln(f"#{space}if defined({name})")
            self.writeln(f"#{space} error {name} is defined")
            self.writeln(f"#{space}endif")

    def generate_test_item(self, macro):
        self.writeln(f"")
        self.writeln(f"// {macro['name']}")
        items = list(reversed(macro['support'][self.impl] or []))

        has_condition = [True] * len(items)
        for index, item in enumerate(items):
            condition = []
            if 'since' in item:
                index = [i for i, [std, _] in enumerate(standards) if std == item['since']][0]
                condition.append(f"__cplusplus > {standards[index - 1][1]}")
            if 'enabled-by' in item:
                o = [to_identifier(option) for option in item['enabled-by'].split()]
                condition.append(' && '.join(o))
            if 'disabled-by' in item:
                o = ['!'+to_identifier(option) for option in item['disabled-by'].split()]
                condition.append(' && '.join(o))
            if 'depends' in item:
                condition.append(f"({item['depends']})")
            if 'pedantic' in item:
                assert item['pedantic'] == False
                condition.append(nonpedantic_option())

            if 'option' in item:
                option = item['option'].split()
                hasopt = [to_identifier(opt) for opt in option]
                hasinvopt = [to_identifier(negate_option(opt)) for opt in option]

                self.start_if(' && '.join([*condition, f"({' || '.join(hasopt)})"]))
                self.generate_positive_test(macro['name'], item['value'])
                self.start_elif(' && '.join([*condition, f"({' || '.join(hasinvopt)})"]))
                self.generate_negative_test(macro['name'])
                self.start_else()
            elif len(condition) > 0:
                self.start_if(' && '.join(condition))
                self.generate_positive_test(macro['name'], item['value'])
                self.start_else()
            else:
                self.generate_positive_test(macro['name'], item['value'])
                has_condition[index] = False

        if len(items) == 0 or has_condition[-1]:
            self.generate_negative_test(macro['name'])

        for index, item in enumerate(items):
            if has_condition[index]:
                self.endif()

    def make_options(self, macro):
        items = macro['support'][self.impl] or []
        opts = [opt for item in items for opt in get_options(item)]
        return [[]] + [[opt, f"-D{to_identifier(opt)}=1"] for opt in opts]

    def pedantic_options(self, macro):
        items = macro['support'][self.impl] or []
        if any('pedantic' in item for item in items):
            return ['-pedantic', f"-D{nonpedantic_option()}=1"]
        else:
            return None
