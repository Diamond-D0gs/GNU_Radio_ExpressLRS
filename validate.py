import os

directory = '/home/gabriel/GNU_Radio_ExpressLRS/results'
packet_count = 1000

file_count = 0
directory_contents = os.listdir(directory)
for file in directory_contents:
    previous_num = -1
    missed_packets = 0
    full_path = os.path.join(directory, file)
    if os.path.isfile(full_path):
        with open(full_path, 'r', encoding='utf-8') as file:
            curr_line = file.readline()
            while len(curr_line) != 0 and previous_num < (packet_count - 1):
                try:
                    curr_num = int(curr_line)
                    diff = curr_num - previous_num
                    previous_num = curr_num
                    missed_packets += (diff - 1)
                except ValueError:
                    missed_packets += 1

                curr_line = file.readline()

        #os.remove(full_path)

    print(f'File {file_count} Missed Packets: {missed_packets}')
    file_count += 1