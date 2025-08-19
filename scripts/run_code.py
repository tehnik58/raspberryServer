import sys
import re
from io import StringIO

# Перехват stdout для реального времени
class RealTimeOutput(StringIO):
    def write(self, text):
        super().write(text)
        # Немедленная отправка вывода
        sys.__stdout__.write(text)
        sys.__stdout__.flush()

sys.stdout = RealTimeOutput()
sys.stderr = RealTimeOutput()

# Чтение кода из stdin до маркера окончания
code_lines = []
end_marker = '__END_OF_CODE__'

print('READY_FOR_CODE')
sys.stdout.flush()

while True:
    line = sys.stdin.readline().rstrip('\n')
    if line == end_marker:
        break
    code_lines.append(line)

user_code = '\n'.join(code_lines)

try:
    # Выполнение пользовательского кода
    exec(user_code)
except Exception as e:
    print(f'Execution error: {str(e)}')
    import traceback
    traceback.print_exc()
finally:
    print('EXECUTION_COMPLETED')