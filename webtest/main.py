import os
from webtest import record
from jinja2 import Environment, PackageLoader
import sys
env = Environment(loader=PackageLoader('webtest', 'templates'))

def generate(host):
    tests = []

    for directory in os.walk(record.testsdir):
        for name in directory[-1]:
            if name == ".gitignore":
                continue
            print("Scanning record {}".format(name))
            try:
                r = record.WebtestRecord(name, host)
                # First, save the result of the fetch
                r.save()
                test_name = "test_{}".format(r.params.title)
                tests.append((test_name, name))
            except:
                print("record {} malformed, skipping".format(name))
    return tests

def gen_class(host, tests):
    tpl = env.get_template('test_class.jinja2')
    hst = host.replace('.', '_')
    testclass = tpl.render(tlist = tests, host = host, hst= hst)
    with open('webtest/tests/test_{}.py'.format(hst), 'w') as fd:
        fd.write(testclass)
        print("Test class generated")

def main():
    hosts = sys.argv[1:]
    for host in hosts:
        tests = generate(host)
        gen_class(host, tests)


if __name__ == '__main__':
    main()
