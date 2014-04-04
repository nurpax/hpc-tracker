
import datetime
import gspread
from xml.dom.minidom import parse
import sys
import re

class ModuleCoverage():
    def __init__(self, name, exprs, toplevel):
        self.name = name
        self.exprs = exprs
        self.toplevel = toplevel

def find(f, seq):
    """Return first item in sequence where f(item) == True."""
    for item in seq:
        if f(item):
            return item
    return None

def read_pass():
    ln = open(".pass").read().splitlines()
    return (ln[0], ln[1])

def parse_module(doc):
    name = doc.attributes["name"].value
    exprs = doc.getElementsByTagName("exprs")[0]
    top = doc.getElementsByTagName("toplevel")[0]
    e = (int(exprs.attributes["count"].value), int(exprs.attributes["boxes"].value))
    t = (int(top.attributes["count"].value), int(top.attributes["boxes"].value))
    return ModuleCoverage(name, e, t)

def top_level_column_name(n):
    return n + " (top-level)"

def exprs_column_name(n):
    return n + " (exprs)"

def sum_tuple((a1,b1), (a2,b2)):
    return (a1+a2, b1+b2)

def main():
    cov_xml = parse(sys.argv[1])
    modules = map(parse_module, cov_xml.getElementsByTagName("module"))

    (login,passwd) = read_pass()
    gc = gspread.login(login, passwd)
    wks = gc.open("hswtrack code coverage").sheet1
    wks.update_cell(1, 1, "Date")
    wks.update_cell(1, 2, "Total (top-level)")
    wks.update_cell(1, 3, "Total (exprs)")

    column_titles = wks.row_values(1)

    # Add new columns if necessary
    new_modules = []
    for module in modules:
        if top_level_column_name(module.name) not in column_titles[3:]:
            new_modules.append(module.name)

    for i in range(len(new_modules)):
        col_idx = len(column_titles)+1+i*2
        wks.update_cell(1, col_idx+0, top_level_column_name(new_modules[i]))
        wks.update_cell(1, col_idx+1, exprs_column_name(new_modules[i]))

    column_titles = wks.row_values(1)

    vals=[]
    vals.append(datetime.datetime.now())
    total_top_level = (0,0)
    total_exprs = (0,0)
    for m in modules:
        total_top_level = sum_tuple(total_top_level, m.toplevel)
        total_exprs     = sum_tuple(total_exprs, m.exprs)
    print ("Total exprs covered/boxes:     %d/%d" % (total_top_level[0], total_top_level[1]))
    print ("Total top-level covered/boxes: %d/%d" % (total_exprs[0], total_exprs[1]))
    vals.append(float(total_top_level[0]) / total_top_level[1])
    vals.append(float(total_exprs[0]) / total_exprs[1])

    col_re = re.compile("(.*)[ ]+\\(")
    for c in column_titles[3:][::2]:
        m = col_re.match(c)
        if m:
            name = m.group(1)
            module = find(lambda mod: mod.name == name, modules)
            (tl_count, tl_total) = module.toplevel
            (e_count, e_total)   = module.exprs

            if tl_total != 0:
                vals.append(float(tl_count) / tl_total)
            else:
                vals.append("")

            if e_total != 0:
                vals.append(float(e_count) / e_total)
            else:
                vals.append("")

    # Find first empty row and insert vals
    for row_idx in range(1,1000):
        if wks.cell(row_idx,1).value is None:
            for idx, v in enumerate(vals):
                wks.update_cell(row_idx, idx+1, v)
            break
    return 0

if __name__ == "__main__":
    sys.exit(main())
