def eval_output(outputfile):
    with open(outputfile, 'rb') as f:
        flines = f.readlines()
        if len(flines) > 0:
            lastline = flines[-1]
            substr = lastline.split(':')
            f.close()
            percentage = substr[1].strip()
            return float(percentage)
        else:
            return -1
    return -1
