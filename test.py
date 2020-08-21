def run1():
    print('run1',check)

def run2():
    print('run2', check2)

def run():
   global check, check2
   check = 'check_var'
   check2 ='check_again'
   run1()
   run2()

if __name__ == "__main__":
   run()
