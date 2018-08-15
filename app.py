#!/bin/env python
#answer = input("Enter a word or phrase: ")
#answer_strip = answer.strip()
import itertools
import time
from datetime import datetime
import os
import math
import threading
from collections import Counter
import operator
from bisect import bisect_left

try:
    from functools import reduce
except:
    pass
cf_enable = False
try:
    import cuckoofilter
    cf_enable = True
except:
    print("This program can use cuckoofilter.")
    print("To install it do something like:")
    print("sudo python3 -m pip install cuckoofilter")
    pass



hunspell_enable = False
try:
    import hunspell
    hunspell_enable = True
except ImportError:
    print("For dictionary words support you must install hunspell ")
    print("module for python first:")
    print("")
    print("Fedora linux Terminal:")
    print("  sudo dnf -y install python3-pyhunspell")
    print("")
    print("Windows:")
    print("  * open command prompt")
    print("  * make sure you have either added python to path (using")
    print("    custom install and Add Python to PATH set to Install")
    print("    before opening command prompt, or cd to your python")
    print("    installation directory)")
    print("  * enter the following commands:")
    print("  python -m pip install CyHunspell")
    print("  * if the command fails, see")
    print("https://stackoverflow.com/questions/35642034/"
          "pip-install-hunspell-cannot-open-include-file-"
          "hunspell-h-no-such-file-or-di")
    time.sleep(2)

try:
    # import Tkinter as tk
    import tkFont
    import ttk
    from Tkinter import *
except ImportError:  # Python 3
    # import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
    from tkinter import *

def npermutations(l):
    # see https://stackoverflow.com/questions/16453188/counting-permuations-in-python
    num = math.factorial(len(l))
    mults = Counter(l).values()
    den = reduce(operator.mul, (math.factorial(v) for v in mults), 1)
    return num / den

def binary_search(l, needle, lo=0, hi=None):
    """can't use 'l' to specify default for hi
    see also https://stackoverflow.com/questions/212358/\
    binary-search-bisection-in-python

    Sequential arguments:
    l -- a list of strings--must be sorted alphabetically
    """
    hi = hi if hi is not None else len(l)  # hi defaults to len(l)
    pos = bisect_left(l, needle, lo, hi)  # find insertion position
    # don't walk off the end:
    return (pos if pos != hi and l[pos] == needle else -1)

def get_second():
    return float(time.time())

class SpellFake:
    def __init__(self):
        self.words = []
        self.words_set = None
        self.cf = None

    def spell(self, word):
        raise RuntimeError("Could not finish SpellFake spell--"
                           "you must call SpellFake bake at least once")

    def spell_binary(self, w):
        # if you got an exception, try running self.fspell.bake()
        # at least once before calling this (not automatic
        # for performance reasons)
        # if word in self.words:
            # return True
        # return False
        return binary_search(self.words, w) >= 0  # must be sorted

    def spell_cuckoo(self, w):
        self.cf.contains(w)

    def bake(self):
        old = self.words
        self.words = []
        print("#adding unique words...")
        unique = {}
        for word in old:
            word_lower = word.lower().strip()
            #if word_lower not in self.words:
            if " " in word_lower:
                print("#WARNING in bake: " + str(word_lower) +
                      "has spaces so splitting")
                for subw in word_lower.split(" "):
                    subw_strip = subw.strip()
                    if len(subw_strip) > 0:
                        unique[subw_strip] = True
            else:
                unique[word_lower] = True
        self.words = list(unique)
        self.words = sorted(self.words)
        self.words_set = set(self.words)
        print("#using " + str(len(self.words)) + " words")
        if cf_enable:
            self.cf = cuckoofilter.CuckooFilter(
                capacity=len(self.words),
                fingerprint_size=1)
            print("# Filling cuckoo filter...")
            for word in self.words:
                self.cf.insert(word)
            print("#   done (cuckoo filter ready)")
            self.spell = self.spell_cuckoo
        else:
            self.spell = spell_binary
        tmp_name = "prev-NoDictAnagram-list.txt"
        outs = open(tmp_name, 'w')
        for word in self.words:
            outs.write(word + "\n")
        outs.close()
        print("wrote " + tmp_name)

    def _get_list(self, path, allow_abbreviations=False,
                    allow_acronyms=False):
        ret = None
        if os.path.isfile(path):
            ret = []
            ins = open(path, 'r')
            ab_count = 0
            ac_count = 0
            line = True
            added_count = 0
            while line:
                line = ins.readline()
                if line:
                    line_strip = line.rstrip()
                    if ((not allow_abbreviations) and
                            ("'" in line_strip)):
                        ab_count += 1
                        continue
                    if not allow_acronyms:
                        if len(line_strip) > 1:
                            if line_strip[1:] != line_strip[1:].lower():
                                ac_count += 1
                                continue
                    if len(line_strip) > 0:
                        ret.append(line_strip)
                        added_count += 1
            ins.close()
            if ac_count > 0:
                print("#Excluded " + str(ac_count) + " acronyms" +
                      " from " + "'" + path + "'")
            if ab_count > 0:
                print("#Excluded " + str(ab_count) + " abbreviations" +
                      " from " + "'" + path + "'")
        return ret
    def append_list(self, path, allow_abbreviations=False,
                    allow_acronyms=False):
        results = self._get_list(
            path,
            allow_abbreviations=allow_abbreviations,
            allow_acronyms=allow_acronyms
        )
        if results is not None:
            self.words.extend(results)

    def append_fixed_width_col(self, path, start, width):
        results = self._get_fixed_width_col(path, start, width)
        if results is not None:
            self.words.extend(results)

    def _get_fixed_width_col(self, path, start, width):
        ret = None
        if os.path.isfile(path):
            ret = []
            ins = open(path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    line_strip = line.rstrip()
                    field = line_strip[start:start+width].strip()
                    if len(field) > 0:
                        ret.append(field)
            ins.close()
        return ret

class AnagramGen:
    def __init__(self):
        self.cancel = False
        self.set_root_data_path(
            os.path.dirname(os.path.realpath(__file__)))
        # above sets self.root_data_path and self.data_paths


        if hunspell_enable:
            hunspell_sub = os.path.join('hunspell_dicts', 'en_US')
            dic_sub = os.path.join(hunspell_sub, 'en_US.dic')
            aff_sub = os.path.join(hunspell_sub, 'en_US.aff')
            dic_path = self.resource_find(dic_sub)
            aff_path = self.resource_find(aff_sub)
            sys_dic_path = '/usr/share/myspell/en_US.dic'
            sys_aff_path = '/usr/share/myspell/en_US.aff'
            local_dic_path = '/usr/local/share/myspell/en_US.dic'
            local_aff_path = '/usr/local/share/myspell/en_US.aff'
            if (dic_path is not None) and (aff_path is not None):
                self.hspell = hunspell.HunSpell(dic_path, aff_path)
            elif (os.path.isfile(sys_dic_path) and
                    os.path.isfile(sys_aff_path)):
                self.hspell = hunspell.HunSpell(sys_dic_path,
                                                sys_aff_path)
                print("#WARNING in AnagramGen init: cannot find own" +
                      "en_US.dic, so using system's '" +
                      sys_dic_path + "'")
            elif (os.path.isfile(local_dic_path) and
                    os.path.isfile(local_aff_path)):
                self.hspell = hunspell.HunSpell(local_dic_path,
                                                local_aff_path)
                print("#WARNING in AnagramGen init: cannot find own" +
                      "en_US.dic, so using locally installed '" +
                      local_dic_path + "'")
            else:
                self.hspell = None
                print("#ERROR in AnagramGen init: cannot generate" +
                      " HunSpell instance since missing en_US.dic")
        else:
            self.hspell = None
            print("#hunspell python module will not be used.")
        # HunSpell object features:
        # * returns True or False (False if misplaced capitalization!):
        #   result = self.hspell.spell('Spooky')  # True
        # * add entry: self.hspell.add('spookie')
        # * remove entry: self.hspell.remove('spookie')
        # * get correct spellings suggestion list: self.hspell.suggest('spookie')
        # * other usage (analyze, stem): https://github.com/blatinier/pyhunspell

        self.fspell = SpellFake()
        lasts_name = 'dist.all.last'
        lasts_path = self.resource_find(lasts_name)
        if lasts_path is not None:
            self.fspell.append_fixed_width_col(lasts_path, 0, 14)
        else:
            print("#WARNING in AnagramGen init: missing " + lasts_name)
        print("#len(self.fspell.words): " + str(len(self.fspell.words)))

        firsts_name = 'census-derived-all-first.txt'
        firsts_path = self.resource_find(firsts_name)
        if firsts_path is not None:
            self.fspell.append_fixed_width_col(firsts_path, 0, 14)
        else:
            print("#WARNING in AnagramGen init: missing " + firsts_name)
        print("#len(self.fspell.words): " + str(len(self.fspell.words)))

        unusual_name = ("app.aspell.net-size=95-American" +
                        "-seldom-stripped-hacker.txt")
        unusual_path = self.resource_find(unusual_name)
        if unusual_path is not None:
            self.fspell.append_list(unusual_path)
        else:
            print("#WARNING in AnagramGen init: missing " +
                  unusual_name)

        self.total_perms = None
        self.spacings = None
        self.old_words = None
        self.block_3_char_words = []
        self.block_4_char_words = []
        self.block_other_words = []  # NOT YET IMPLEMENTED
        block_name = 'blocked.txt'
        block_path = self.resource_find(block_name)
        if block_path is not None:
            ins = open(block_path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    line_strip = line.strip()
                    if len(line_strip) == 4:
                        self.block_4_char_words.append(line_strip)
                    elif len(line_strip) == 3:
                        self.block_3_char_words.append(line_strip)
                    elif len(line_strip) > 0:
                        self.block_other_words.append(line_strip)
            if len(self.block_other_words) > 0:
                print("#WARNING: self.block_other_words" +
                      "(length " + str(len(self.block_other_words)) +
                      ") is not yet implemented.")
            print("#block 3-letter list length: " +
                  str(len(self.block_3_char_words)))
            print("#block 4-letter list length: " +
                  str(len(self.block_4_char_words)))
            ins.close()
        else:
            print("#WARNING in AnagramGen init: missing '" + block_name +
                  "'")

    def set_root_data_path(self, path):
        self.root_data_path = path
        self._regenerate_data_paths()

    def _regenerate_data_paths(self):
        self.data_paths = ['.', self.root_data_path]
                           # os.path.join(self.root_data_path, 'words')]

    def resource_find(self, sub_path):
        try_path = None
        for this_data_path in self.data_paths:
            if this_data_path != ".":
                try_path = os.path.join(this_data_path, sub_path)
            else:
                try_path = sub_path
            if os.path.isfile(try_path):
                return try_path
        return None

    def generate_meta(self, answer):
        answer_strip = answer.strip()
        answer_strip_lower = answer_strip.lower()
        # print(str(result))
        self.spacings = []
        spaces = []
        for i in range(len(answer_strip_lower)):
            c = answer_strip_lower[i]
            if c == ' ':
                spaces.insert(0, i)

        print("#spaces: " + str(spaces))
        while "  " in answer_strip_lower:
            answer_strip_lower = answer_strip_lower.replace("  ", " ")
        self.old_words = answer_strip_lower.split(" ")

        chunks = []
        i = 0
        self.unique = {}
        for w in self.old_words:
            if i != 0:
                chunks.append(" ")
            chunks.append(w)
            i += 1

        for spacing in itertools.permutations(chunks):
            spacing_s = ""
            prev_s = None
            word_i = 0  # keep words in order so extras aren't created
            for s in spacing:
                if s == ' ':
                    if (prev_s is None) or (prev_s != ' '):
                        spacing_s += s
                else:
                    spacing_s += self.old_words[word_i]
                    word_i += 1
            while "  " in spacing_s:
                spacing_s = spacing_s.replace("  ", " ")
            self.unique[spacing_s.strip()] = True

        self.spacings = list(self.unique)
        # for remove_count in range(len(spaces)):
            # result = answer_strip_lower
            # count = 0
            # if remove_count > 0:
                # for i in spaces:
                    # result = result[:i] + result[i+1:]
                    # count += 1
                    # if count > remove_count:
                        # break
            # self.spacings.append(result)

        print("#self.spacings (where spaces are does not matter here,"
              " only quantity, since spaces will be rearranged along"
              " with characters):")

        self.total_perms = 0
        for version in self.spacings:
            print("#  " + version)
            self.total_perms += npermutations(version)

        print("#permutations: " + str(self.total_perms))
        self.total_perms *= 2  # not sure why this is needed
        print("#effective permutations: " + str(self.total_perms))

    #for s in itertools.permutations(answer_strip_lower):
    #    ok = True
    #    print(s)

    def is_dic_word(self, w, one_char_words=[],
                    two_char_words=[]):
        ret = False
        """Check if is dictionary word, with given exceptions.
        (uses params and the following class members:
        self.block_3_char_words, self.block_4_char_words)

        Keyword arguments:
        one_char_words -- This is only used if use_fake_words
                            is True. When len(candidate) is 1, only allow
                            the word to be a word if in this list.
                            If this is None, the check is not done.
        two_char_words -- Causes same behavior as one_char_words except
                          when len(candidate) is 2.

        """
        if (len(w) > 0) and (self.hspell.spell(w)):
            if len(w) == 1:
                if one_char_words is not None:
                    if w in one_char_words:
                        ret = True
                else:
                    ret = True
            elif len(w) == 2:
                if two_char_words is not None:
                    if w in two_char_words:
                        ret = True
                else:
                    ret = True
            elif len(w) == 3:
                if self.block_3_char_words is not None:
                    if w not in self.block_3_char_words:
                        ret = True
                else:
                    ret = True
            elif len(w) == 4:
                if self.block_4_char_words is not None:
                    if w not in self.block_4_char_words:
                        ret = True
                else:
                    ret = True
            else:
                ret = True
        return ret

    def is_fake_word(self, word):
        return self.fspell.spell(word)

    def is_fake_word(self, word):
        return self.fspell.spell(word)

    def is_word(self, word):
        return self.is_dic_word(word) or self.is_fake_word(word)

    # def always_true(word):
        # return True

    def stop(self):
        self.cancel = True

    def start(self, callback_pb, allow_original_words=False,
              use_fake_words=True, use_dictionary=False,
              all_must_be_words=False):
        self.cancel = False
        """Start printing anagrams to standard output
        allow_original_words -- if True, allow word or word from phrase
                                given originally by user
        use_fake_words -- use included list of words and names
        use_dictionary -- use hunspell dictionary if available
        all_must_be_words -- Only keep the anagram if all words in the
                             anagram are actually words (requires
                             use_fake_words or use_dictionary or both).
        """
        answer = e.get()
        self.fspell.bake()
        print("# AnagramGen start")
        self.generate_meta(answer)
        callback_pb['value'] = 0
        callback_pb['maximum'] = self.total_perms
        # root.update_idletasks()
        # callback_pb["value"] += 1
        if not allow_original_words:
            show_overview("* excluding results containing old words: " +
                  str(self.old_words))
        show_overview("* there are " +
                      str(self.total_perms) +
                      " possible combinations...")
        wait_count = 0
        max_wait_count = 8000
        max_wait_s = 5.0
        start_time = get_second()
        # etaLabel['text'] = "start time: " + str(start_time)
        etaLabel['text'] = "estimating time remaining"
        prev_time = start_time
        step_count = 0
        keep_count = 0
        prev_passed_h_i = None
        prev_passed_d_i = None
        eta_number = 1
        gen_count = None
        good_count = None
        if self.hspell is None:
            use_dictionary = False
        check_method = None
        check_any = True
        if use_dictionary and use_fake_words:
            check_method = self.is_word
        elif use_dictionary:
            check_method = self.is_dic_word
        elif use_fake_words:
            check_method = self.is_fake_word
        else:
            check_any = False
            show_overview("* not limiting to words (no use_dictionary,"
                  " no use_fake_words).")
            # check_method = self.always_true

        show_overview("See console for results.")
        for version in self.spacings:
            if self.cancel:
                return
            show_overview("finding anagrams of " + version + "...")
            for s_tuple in itertools.permutations(version):
                if self.cancel:
                    return
                s = ""
                prev_c = None
                for c in s_tuple:
                    c_keep = True
                    if c == ' ':
                        if prev_c == ' ':
                            c_keep = False
                    if c_keep:
                        s += c
                    prev_c = c
                keep = True
                if not allow_original_words:
                    for word in self.old_words:
                        if word in s:
                            keep = False
                found_w = None
                if keep:
                    if check_any:
                        found_words = s.split(" ")
                        if all_must_be_words:
                            gen_count = len(found_words)
                            good_count = 0
                            for w in found_words:
                                if check_method(w):
                                    found_w = w
                                    good_count += 1
                            if good_count < gen_count:
                                keep = False
                        else:
                            for w in found_words:
                                if check_method(w):
                                    found_w = w
                                    good_count = 1
                                    break

                            if found_w is None:
                                keep = False

                if keep:
                    keep_count += 1
                    # if found_w is not None:
                        # print(s + "  #" + found_w)
                    # else:
                    print(s)

                # wait_count += 1
                # if wait_count >= max_wait_count:
                if get_second() - prev_time >= max_wait_s:
                    wait_count = 0
                    progress = (float(callback_pb["value"]) /
                                float(self.total_perms))
                    remaining = 1.0 - progress
                    passed = get_second() - start_time
                    if progress > 0.0:
                        est_total_s = passed / progress
                        est_remaining_s = remaining * est_total_s
                        s_f = est_remaining_s
                        m_f = s_f/60.0
                        h_f = m_f/60.0
                        d_f = h_f/24.0
                        y_f = d_f/365.25
                        y_i = int(y_f)
                        d_i = int(d_f)
                        h_i = int(h_f)
                        m_i = int(m_f)
                        s_i = int(s_f)
                        passed_m_f = passed/60.0
                        passed_m_i = int(passed_m_f)
                        passed_h_f = passed_m_f/60.0
                        passed_h_i = int(passed_h_f)
                        passed_d_f = passed_h_f/24.0
                        passed_d_i = int(passed_d_f)
                        prefix = ("#(" + str(keep_count) +
                                  " kept) ETA after " +
                                  str(int(passed)) + "s: ")
                        msg = prefix + str(s_i) + " seconds"
                        if y_i > 0:
                            msg = (prefix + "{0:.2f}".format(y_f) +
                                   " years")
                            if ((prev_passed_d_i is None) or
                                    (passed_d_i != prev_passed_d_i)):
                                # show progress daily:
                                print("#current:" + str(datetime.now()))
                                print("#progress:" + str(progress))
                        elif d_i > 0:
                            msg = (prefix + "{0:.2f}".format(d_f) +
                                   " days")
                            if ((prev_passed_h_i is None) or
                                    (passed_h_i != prev_passed_h_i)):
                                # show progress hourly:
                                print("#current:" + str(datetime.now()))
                                print("#progress:" + str(progress))
                        elif h_i > 0:
                            msg = (prefix + "{0:.2f}".format(h_f) +
                                   " hours")
                        elif m_i > 0:
                            msg = (prefix + "{0:.2f}".format(m_f) +
                                   " minutes")
                        etaLabel['text'] = msg
                        prev_passed_h_i = passed_h_i
                        prev_passed_d_i = passed_d_i
                        eta_number += 1
                    prev_time = get_second()

                callback_pb.step(1)
                step_count += 1
        etaLabel['text'] = ""

        show_overview("done (checked:" + str(step_count) +
                      " kept:" + str(keep_count) + ")!")

if __name__ == "__main__":
    ag = AnagramGen()
    root = Tk()
    anagram_t = None

    def start(pb):
        ag.start(pb)
        stopButton.pack_forget()
        beginButton.pack()

    def stop_thread():
        global anagram_t
        stopButton.pack_forget()
        beginButton.pack()
        ag.stop()
        # see also https://stackoverflow.com/questions/15729498/
        # how-to-start-and-stop-thread
        show_overview("Cancelled by user.")
        etaLabel['text'] = ""
        pb['value'] = 0

    def start_thread():
        global anagram_t
        beginButton.pack_forget()
        stopButton.pack()
        anagram_t = threading.Thread(target=start, args=(pb,))
        anagram_t.start()

    def quit():
        global root
        root.destroy()

    def show_overview(msg):
        msgLabel = Label(frame, text=msg)
        msgLabel.pack()

    # frame = Frame(root, highlightbackground="yellow",
    #                    highlightcolor="red", highlightthickness=4,
    #                    width=800, height=600, bd=0)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    frame = Frame(root, width=screen_width/2,
                       height=screen_height/2)
    frame.pack(expand=1, fill=BOTH)
    frame.pack_propagate(False)
    # frame.geometry('800x600')
    etaLabel = Label(frame, text="")
    etaLabel.pack()
    # MOVE window:
    root.geometry("+" + str(int(screen_width/4)) + "+" +
                  str(int(screen_height/4)))

    root.wm_title("nodictanagram by poikilos")

    pb = ttk.Progressbar(frame, orient="horizontal", length=200,
                         mode="determinate")
    pb.pack()
    pb["value"] = 0
    pb["maximum"] = 100
    # pb.start  # will show a looping progress bar

    e = Entry(frame)
    # takes approx 11 yrs on Intel i7 4770 K :)
    #e.insert(END, 'The cows are sick')

    # e.delete(0, END)
    # e.insert(END, 'is mud')
    # e.insert(END, 'far flung')
    #e.insert(END, 'hangry cat')
    e.insert(END, 'Jake Gustafson')
    e.pack()

    beginButton = Button(
        frame,
        text="Begin",
        command=start_thread)
    beginButton.pack()
    stopButton = Button(
        frame,
        text="Stop",
        command=stop_thread)


    root.mainloop()

