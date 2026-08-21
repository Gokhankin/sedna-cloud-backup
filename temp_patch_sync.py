with open('sedna_sync.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = '''                # In-House: only include if Status == 2 (currently checked in) OR (status == 1 and checkin < date_str and checkout > date_str)
                if status == 2 and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)
                elif status == 1 and checkin < date_str and checkout > date_str:
                    # Expected in-house on future day after arrival
                    inh_list.append(r_copy)'''

new_block = '''                # In-House / Occupied on future date: CheckinDate <= date_str AND CheckOutDate > date_str AND Status IN (1, 2)
                if status in (1, 2) and checkin <= date_str and checkout > date_str:
                    inh_list.append(r_copy)'''

if old_block in code:
    code = code.replace(old_block, new_block)
    print("Successfully patched future in-house logic in sedna_sync.py!")
else:
    print("Target block not found in sedna_sync.py!")

with open('sedna_sync.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved updated sedna_sync.py!")
