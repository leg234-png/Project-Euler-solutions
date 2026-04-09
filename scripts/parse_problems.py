import json
import os
import re

def parse_problems(filepath):
    # Offsets based on header analysis
    OFFSETS = {
        'id': (0, 4),
        'title': (4, 24),
        'subtitle': (24, 33),
        'content': (33, 238),
        'html_content': (238, 342),
        'release_date': (342, 355),
        'solved_by_count': (355, 371),
        'difficulty': (371, 400)
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Step 1: Segmentation based on logical boundaries
    segments = []
    current_segment = []
    
    for i, line in enumerate(lines[1:]): # Skip header
        if len(line) < 238:
            if current_segment:
                segments.append(current_segment)
                current_segment = []
            continue
            
        html_part = line[OFFSETS['html_content'][0]:OFFSETS['html_content'][1]].strip()
        
        # New segment if </p> followed by <p>
        is_split = False
        if i > 0 and html_part.startswith('<p>'):
            # Check previous line of ACTUAL content
            prev_idx = i # lines[i] is the previous one in lines[1:]
            prev_html = lines[prev_idx][OFFSETS['html_content'][0]:OFFSETS['html_content'][1]].strip()
            if prev_html.endswith('</p>'):
                is_split = True
        
        if is_split and current_segment:
            segments.append(current_segment)
            current_segment = []
            
        current_segment.append(line)
        
    if current_segment:
        segments.append(current_segment)

    # Step 2: Extract IDs for each segment and identify orphans
    segment_info = []
    all_ids = set()
    
    for seg in segments:
        seg_id = None
        seg_title = ""
        seg_html = ""
        has_plain_text = False
        
        for line in seg:
            ic = line[OFFSETS['id'][0]:OFFSETS['id'][1]].strip()
            sc = line[OFFSETS['subtitle'][0]:OFFSETS['subtitle'][1]].strip()
            tc = line[OFFSETS['title'][0]:OFFSETS['title'][1]].strip()
            cc = line[OFFSETS['content'][0]:OFFSETS['content'][1]].strip()
            
            if ic.isdigit(): seg_id = int(ic)
            elif sc.isdigit() and seg_id is None: seg_id = int(sc)
            if tc and tc.lower() != "problem":
                if seg_title: seg_title += " "
                seg_title += tc
            if cc: has_plain_text = True
            
            seg_html += line[OFFSETS['html_content'][0]:OFFSETS['html_content'][1]]
        
        info = {'id': seg_id, 'title': seg_title, 'html': seg_html, 'has_plain': has_plain_text}
        segment_info.append(info)
        if seg_id: all_ids.add(seg_id)

    # Step 3: Associate orphans and combine
    final_data = {pid: {'title': '', 'html': ''} for pid in all_ids}
    
    for i, info in enumerate(segment_info):
        target_id = info['id']
        
        if target_id is None:
            # Heuristic: 
            # If it has plain text, it's likely a continuation of the PREVIOUS ID.
            # If it has NO plain text, it's likely an intro to the NEXT ID.
            if info['has_plain']:
                # Look back
                for j in range(i - 1, -1, -1):
                    if segment_info[j]['id']:
                        target_id = segment_info[j]['id']
                        break
            else:
                # Look ahead
                for j in range(i + 1, len(segment_info)):
                    if segment_info[j]['id']:
                        target_id = segment_info[j]['id']
                        break
        
        if target_id:
            if info['title']:
                if final_data[target_id]['title']: final_data[target_id]['title'] += " "
                final_data[target_id]['title'] += info['title']
            final_data[target_id]['html'] += " " + info['html']

    # Final cleanup
    results = {}
    for pid, data in final_data.items():
        results[pid] = {
            'title': re.sub(r'\s+', ' ', data['title']).strip(),
            'html_content': re.sub(r'\s+', ' ', data['html']).strip()
        }

    return results

    return results

    return results

if __name__ == "__main__":
    input_file = "problems.txt"
    output_file = "problems_data.json"
    
    print(f"Parsing {input_file}...")
    data = parse_problems(input_file)
    print(f"Parsed {len(data)} problems.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {output_file}")
