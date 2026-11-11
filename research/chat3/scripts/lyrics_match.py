#!/usr/bin/env python3
"""Song/lyric matching from authorised (public-domain) text only.

No scraping and no copyrighted lyrics: the test corpus is 40 King James Version
verses (public domain), used as a stand-in for lyric lines so the matcher can be
exercised end-to-end.
"""
import hashlib
import json
import os
import random
import re
import sys

VERSES = {
    'John 3:16': 'For God so loved the world that he gave his only begotten Son that whosoever believeth in him should not perish but have everlasting life',
    'Psalms 23:1': 'The LORD is my shepherd I shall not want',
    'Genesis 1:1': 'In the beginning God created the heaven and the earth',
    'Philippians 2:5': 'Let this mind be in you which was also in Christ Jesus',
    'Romans 8:28': 'And we know that all things work together for good to them that love God',
    'Isaiah 41:10': 'Fear thou not for I am with thee be not dismayed for I am thy God',
    'Jeremiah 29:11': 'For I know the thoughts that I think toward you thoughts of peace and not of evil',
    'Matthew 11:28': 'Come unto me all ye that labour and are heavy laden and I will give you rest',
    'John 14:6': 'Jesus saith unto him I am the way the truth and the life no man cometh unto the Father but by me',
    'Proverbs 3:5': 'Trust in the LORD with all thine heart and lean not unto thine own understanding',
    'Hebrews 11:1': 'Now faith is the substance of things hoped for the evidence of things not seen',
    'Psalms 46:1': 'God is our refuge and strength a very present help in trouble',
    'Matthew 6:33': 'But seek ye first the kingdom of God and his righteousness and all these things shall be added unto you',
    'John 1:1': 'In the beginning was the Word and the Word was with God and the Word was God',
    'Acts 1:8': 'But ye shall receive power after that the Holy Ghost is come upon you',
    'Romans 12:2': 'And be not conformed to this world but be ye transformed by the renewing of your mind',
    'Galatians 5:22': 'But the fruit of the Spirit is love joy peace longsuffering gentleness goodness faith',
    'Ephesians 2:8': 'For by grace are ye saved through faith and that not of yourselves it is the gift of God',
    'Psalms 91:1': 'He that dwelleth in the secret place of the most High shall abide under the shadow of the Almighty',
    'Isaiah 40:31': 'But they that wait upon the LORD shall renew their strength',
    'Matthew 5:16': 'Let your light so shine before men that they may see your good works',
    'John 15:5': 'I am the vine ye are the branches he that abideth in me and I in him',
    'Romans 5:8': 'But God commendeth his love toward us in that while we were yet sinners Christ died for us',
    'Psalms 119:105': 'Thy word is a lamp unto my feet and a light unto my path',
    '2 Timothy 1:7': 'For God hath not given us the spirit of fear but of power and of love and of a sound mind',
    'Joshua 1:9': 'Be strong and of a good courage be not afraid neither be thou dismayed',
    '1 Corinthians 13:4': 'Charity suffereth long and is kind charity envieth not charity vaunteth not itself',
    'Philippians 4:13': 'I can do all things through Christ which strengtheneth me',
    'Psalms 27:1': 'The LORD is my light and my salvation whom shall I fear',
    'Isaiah 53:5': 'But he was wounded for our transgressions he was bruised for our iniquities',
    'John 10:10': 'The thief cometh not but for to steal and to kill and to destroy',
    'Matthew 28:19': 'Go ye therefore and teach all nations baptizing them in the name of the Father',
    'Romans 10:9': 'That if thou shalt confess with thy mouth the Lord Jesus and shalt believe in thine heart',
    'Hebrews 4:12': 'For the word of God is quick and powerful and sharper than any twoedged sword',
    'James 1:5': 'If any of you lack wisdom let him ask of God that giveth to all men liberally',
    '1 Peter 5:7': 'Casting all your care upon him for he careth for you',
    'Psalms 34:8': 'O taste and see that the LORD is good blessed is the man that trusteth in him',
    'Isaiah 26:3': 'Thou wilt keep him in perfect peace whose mind is stayed on thee',
    'Matthew 4:4': 'It is written Man shall not live by bread alone but by every word that proceedeth out of the mouth of God',
    'Revelation 21:4': 'And God shall wipe away all tears from their eyes',
}

HOLDOUT = [
    'Amazing grace how sweet the sound that saved a wretch like me',
    'Holy holy holy Lord God Almighty early in the morning our song shall rise to thee',
]


def tokens(text):
    text = text.lower().replace('\u2019', "'")
    return [t for t in re.split(r"[^a-z0-9']+", text) if t]


def fingerprints(text, n=4):
    ts = tokens(text)
    return {hashlib.sha1(' '.join(ts[i:i + n]).encode()).hexdigest()[:16]
            for i in range(max(0, len(ts) - n + 1))}


class LyricIndex:
    def __init__(self, corpus):
        self.postings = {}
        self.lines = {}
        for line_id, text in corpus.items():
            fps = fingerprints(text)
            self.lines[line_id] = fps
            for fp in fps:
                self.postings.setdefault(fp, set()).add(line_id)

    def match(self, query, min_score=0.18):
        q = fingerprints(query)
        if not q:
            return None, 0.0
        scores = {}
        for fp in q:
            for line_id in self.postings.get(fp, ()):
                scores[line_id] = scores.get(line_id, 0) + 1
        if not scores:
            return None, 0.0
        best = max(scores, key=scores.get)
        score = scores[best] / len(q)
        return (best, score) if score >= min_score else (None, score)


def corrupt(text, rate, rng):
    ts = tokens(text)
    for i in range(len(ts)):
        if rng.random() < rate:
            ts[i] = rng.choice(['the', 'and', 'lord', 'grace', 'amen', 'zzz'])
    return ' '.join(ts)


def main():
    rng = random.Random(11)
    index = LyricIndex(VERSES)
    rows = []
    for rate, label in [(0.0, 'exact'), (0.10, 'err10'), (0.25, 'err25')]:
        hits = 0
        for line_id, text in VERSES.items():
            q = text if rate == 0 else corrupt(text, rate, rng)
            got, score = index.match(q)
            hits += int(got == line_id)
        rows.append({'set': label, 'n': len(VERSES), 'top1': hits,
                     'top1_pct': round(100 * hits / len(VERSES), 1)})
    fp = 0
    for text in HOLDOUT:
        got, score = index.match(text)
        fp += int(got is not None)
    rows.append({'set': 'holdout_negative', 'n': len(HOLDOUT), 'top1': len(HOLDOUT) - fp,
                 'top1_pct': round(100 * (len(HOLDOUT) - fp) / len(HOLDOUT), 1)})
    print(json.dumps(rows, indent=1))
    os.makedirs('out', exist_ok=True)
    with open('out/lyrics_match.json', 'w') as f:
        json.dump(rows, f, indent=2)


if __name__ == '__main__':
    sys.exit(main())
