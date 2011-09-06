# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Parses and tokenizes LilyPond input.
"""

from __future__ import unicode_literals

import itertools

from . import _token
from . import Parser, FallthroughParser


re_articulation = r"[-_^][_.>|+^-]"
re_dynamic = r"\\(f{1,5}|p{1,5}|mf|mp|fp|spp?|sff?|sfz|rfz)\b|\\[<!>]"

re_duration = r"(\\(maxima|longa|breve)\b|(1|2|4|8|16|32|64|128|256|512|1024|2048)(?!\d))"
re_dot = r"\."
re_scaling = r"\*[\t ]*\d+(/\d+)?"


class Variable(_token.Token):
    pass


class UserVariable(_token.Token):
    pass


class Value(_token.Item, _token.Numeric):
    pass


class DecimalValue(Value):
    rx = r"-?\d+(\.\d+)?"


class Fraction(Value):
    rx = r"\d+/\d+"
    
    
class Error(_token.Error):
    pass


class Comment(_token.Comment):
    pass


class BlockCommentStart(Comment, _token.BlockCommentStart, _token.Indent):
    rx = r"%{"
    def updateState(self, state):
        state.enter(BlockCommentParser())


class BlockCommentEnd(Comment, _token.BlockCommentEnd, _token.Leaver, _token.Dedent):
    rx = r"%}"


class BlockCommentSpace(Comment, _token.BlockComment, _token.Space):
    pass


class LineComment(Comment, _token.LineComment):
    rx = r"%.*$"
    

class String(_token.String):
    pass


class StringQuotedStart(String, _token.StringStart):
    rx = r'"'
    def updateState(self, state):
        state.enter(StringParser())
        

class StringQuotedEnd(String, _token.StringEnd):
    rx = r'"'
    def updateState(self, state):
        state.leave()
        state.endArgument()


class StringQuoteEscape(_token.Character):
    rx = r'\\[\\"]'


class Skip(_token.Token):
    rx = r"(\\skip|s)(?![A-Za-z])"
    
    
class Rest(_token.Token):
    rx = r"[Rr](?![A-Za-z])"
    
    
class Note(_token.Token):
    rx = r"[a-z]+(?![A-Za-z])"
    

class Duration(_token.Token):
    pass


class DurationStart(Duration):
    rx = re_duration
    def updateState(self, state):
        state.enter(DurationParser())


class Dot(Duration):
    rx = re_dot
    
    
class Scaling(Duration):
    rx = re_scaling
    
    
class Delimiter(_token.Token):
    pass


class OpenBracket(Delimiter, _token.MatchStart, _token.Indent):
    """An open bracket, does not enter different parser, subclass or reimplement Parser.updateState()."""
    rx = r"\{"
    matchname = "bracket"


class CloseBracket(Delimiter, _token.MatchEnd, _token.Dedent):
    rx = r"\}"
    matchname = "bracket"
    def updateState(self, state):
        state.leave()
        state.endArgument()    
    

class OpenSimultaneous(Delimiter, _token.MatchStart, _token.Indent):
    """An open double French quote, does not enter different parser, subclass or reimplement Parser.updateState()."""
    rx = r"<<"
    matchname = "simultaneous"


class CloseSimultaneous(Delimiter, _token.MatchEnd, _token.Dedent):
    rx = r">>"
    matchname = "simultaneous"
    def updateState(self, state):
        state.leave()
        state.endArgument()
    

class SequentialStart(OpenBracket):
    def updateState(self, state):
        state.enter(LilyPondParserMusic())


class SequentialEnd(CloseBracket):
    pass


class SimultaneousStart(OpenSimultaneous):
    def updateState(self, state):
        state.enter(LilyPondParserMusic())


class SimultaneousEnd(CloseSimultaneous):
    pass


class Articulation(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(itertools.chain(
            words.articulations,
            words.ornaments,
            words.fermatas,
            words.instrument_scripts,
            words.repeat_scripts,
            words.ancient_scripts,
        )))
    
    
class Direction(Articulation):
    rx = r"[-_^]"
    def updateState(self, state):
        state.enter(ScriptAbbreviationParser())


class ScriptAbbreviation(Articulation, _token.Leaver):
    rx = r"[+|>._^-]"


class Slur(_token.Token):
    pass


class SlurStart(Slur, _token.MatchStart):
    rx = r"\("
    matchname = "slur"
    

class SlurEnd(Slur, _token.MatchEnd):
    rx = r"\)"
    matchname = "slur"
    

class PhrasingSlurStart(SlurStart):
    rx = r"\\\("
    matchname = "phrasingslur"
    
    
class PhrasingSlurEnd(SlurEnd):
    rx = r"\\\)"
    matchname = "phrasingslur"
    

class Tie(Slur):
    rx = r"~"


class Beam(_token.Token):
    pass


class BeamStart(Beam, _token.MatchStart):
    rx = r"\["
    matchname = "beam"


class BeamEnd(Beam, _token.MatchEnd):
    rx = r"\]"
    matchname = "beam"


class Ligature(_token.Token):
    pass


class LigatureStart(Ligature, _token.MatchStart):
    rx = r"\\\["
    matchname = "ligature"
    
    
class LigatureEnd(Ligature, _token.MatchEnd):
    rx = r"\\\]"
    matchname = "ligature"
    
    
class Keyword(_token.Item):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_keywords))


class VoiceSeparator(Delimiter):
    rx = r"\\\\"
    

class Dynamic(_token.Token):
    rx = re_dynamic


class Command(_token.Item):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_music_commands))
    

class Specifier(_token.Token):
    # a specifier of a command e.g. the name of clef or repeat style.
    pass


class Score(Keyword):
    rx = r"\\score\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectScore())
        

class Book(Keyword):
    rx = r"\\book\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectBook())
        
        
class BookPart(Keyword):
    rx = r"\\bookpart\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectBookPart())


class Paper(Keyword):
    rx = r"\\paper\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectPaper())


class Header(Keyword):
    rx = r"\\header\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectHeader())


class Layout(Keyword):
    rx = r"\\layout\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectLayout())


class Midi(Keyword):
    rx = r"\\midi\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectMidi())


class With(Keyword):
    rx = r"\\with\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectWith())


class LayoutContext(Keyword):
    rx = r"\\context\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectContext())


class Markup(Command):
    rx = r"\\markup(?![A-Za-z])"
    def updateState(self, state):
        state.enter(MarkupParser(1))


class MarkupLines(Markup):
    rx = r"\\markuplines(?![A-Za-z])"
    def updateState(self, state):
        state.enter(MarkupParser(1))


class MarkupCommand(Markup):
    rx = r"\\[A-Za-z]+(-[A-Za-z]+)*(?![A-Za-z])"
    def updateState(self, state):
        import ly.words
        command = self[1:]
        if command in ly.words.markupcommands_nargs[0]:
            state.endArgument()
        else:
            for argcount in 2, 3, 4:
                if command in ly.words.markupcommands_nargs[argcount]:
                    break
            else:
                argcount = 1
            state.enter(MarkupParser(argcount))


class MarkupScore(Markup):
    rx = r"\\score\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectScore())


class MarkupWord(_token.Item):
    rx = r'[^{}"\\\s#%]+'


class OpenBracketMarkup(OpenBracket):
    def updateState(self, state):
        state.enter(MarkupParser())


class CloseBracketMarkup(CloseBracket):
    def updateState(self, state):
        state.endArgument()    
        state.leave()
        state.endArgument()    


class Repeat(Command):
    rx = r"\\repeat(?![A-Za-z])"
    def updateState(self, state):
        state.enter(RepeatParser())
    
    
class RepeatSpecifier(Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})(?![A-Za-z])".format("|".join(words.repeat_types))
    

class RepeatStringSpecifier(String, Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r'"({0})"'.format("|".join(words.repeat_types))
    

class RepeatCount(Value, _token.Leaver):
    rx = r"\d+"


class Override(Keyword):
    rx = r"\\override\b"
    def updateState(self, state):
        state.enter(LilyPondParserOverride())


class Set(Override):
    rx = r"\\set\b"
    def updateState(self, state):
        state.enter(LilyPondParserSet())
    

class Revert(Override):
    rx = r"\\revert\b"
    def updateState(self, state):
        state.enter(LilyPondParserRevert())
    

class DotSetOverride(Delimiter):
    rx = r"\."


class Unset(Keyword):
    rx = r"\\unset\b"
    def updateState(self, state):
        state.enter(LilyPondParserUnset())


class New(Command):
    rx = r"\\new\b"
    def updateState(self, state):
        state.enter(LilyPondParserNewContext())
        
        
class Context(New):
    rx = r"\\context\b"
    

class Change(New):
    rx = r"\\change\b"
    
    
class Clef(Command):
    rx = r"\\clef"
    def updateState(self, state):
        state.enter(LilyPondParserClef())


class ClefSpecifier(Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.clefs_plain))
    

class Unit(Command):
    rx = r"\\(mm|cm|in|pt)\b"
    

class InputMode(Command):
    pass


class LyricMode(InputMode):
    rx = r"\\(lyricmode|((old)?add)?lyrics|lyricsto)\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectLyricMode())


class Lyric(_token.Item):
    """Base class for Lyric items."""


class LyricText(Lyric):
    rx = r"[^\\\s\d~\"]+"


class LyricHyphen(Lyric):
    rx = r"--"
    
    
class LyricExtender(Lyric):
    rx = r"__"
    
    
class LyricSkip(Lyric):
    rx = r"_"
    

class LyricTie(Lyric):
    rx = r"~"


class NoteMode(InputMode):
    rx = r"\\(notes|notemode)\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectNoteMode())


class ChordMode(InputMode):
    rx = r"\\(chords|chordmode)\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectChordMode())


class DrumMode(InputMode):
    rx = r"\\(drums|drummode)\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectDrumMode())


class FigureMode(InputMode):
    rx = r"\\(figures|figuremode)\b"
    def updateState(self, state):
        state.enter(LilyPondParserExpectFigureMode())


class UserCommand(_token.Token):
    rx = r"\\[A-Za-z]+(?![A-Za-z])"
    
    
class SchemeStart(_token.Item):
    rx = "[#$]"
    def updateState(self, state):
        import scheme
        state.enter(scheme.SchemeParser(1))


class ContextName(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.contexts))
    

class BackSlashedContextName(ContextName):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})\b".format("|".join(words.contexts))
    
    
class GrobName(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.grobs))


class ContextProperty(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import data
        return r"\b({0})\b".format("|".join(data.context_properties()))


class PaperVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.papervariables))


class HeaderVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.headervariables))


class LayoutVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.layoutvariables))


class Chord(_token.Token):
    """Base class for Chord delimiters."""
    pass


class ChordStart(Chord):
    rx = r"<"
    def updateState(self, state):
        state.enter(LilyPondParserChord())


class ChordEnd(Chord, _token.Leaver):
    rx = r">"
    

class ErrorInChord(_token.Error):
    rx = "|".join((
        re_articulation, # articulation
        r"<<|>>", # double french quotes
        r"\\[\\\]\[\(\)()]", # slurs beams
    ))
    

class Name(UserVariable):
    """A variable name without \\ prefix."""
    rx = r"[a-zA-Z]+(?![a-zA-Z])"
    

class NameLower(Name):
    """A lowercase name."""
    rx = r"[a-z]+(?![a-zA-Z])"
    
    
class NameHyphenLower(Name):
    """A lowercase name that may contain hyphens."""
    rx = r"[a-z]+(-[a-z]+)*(!?[-a-zA-Z])"
    

class EqualSign(_token.Token):
    rx = r"="
    

class EqualSignSetOverride(EqualSign):
    """An equal sign in a set/override construct."""
    def updateState(self, state):
        # wait for one more expression, then leave
        state.parser().argcount = 1



# Parsers
class LilyPondParser(Parser):
    mode = 'lilypond'

# basic stuff that can appear everywhere
space_items = (
    _token.Space,
    BlockCommentStart,
    LineComment,
)    


base_items = space_items + (
    SchemeStart,
    StringQuotedStart,
)


# items that represent commands in both toplevel and music mode
command_items = (
    Repeat,
    Override, Revert,
    Set, Unset,
    New, Context,
    With,
    Clef,
    ChordMode, DrumMode, FigureMode, LyricMode, NoteMode,
    Markup,
    MarkupLines,
    Keyword,
    Command,
    UserCommand,
)


# items that occur in toplevel, book, bookpart or score
# no Leave-tokens!
toplevel_base_items = base_items + (
    Fraction,
    SequentialStart,
    SimultaneousStart,
) + command_items


# items that occur in music expressions
music_items = base_items + (
    Dynamic,
    Skip,
    Rest,
    Note,
    Fraction,
    DurationStart,
    VoiceSeparator,
    SequentialStart, SequentialEnd,
    SimultaneousStart, SimultaneousEnd,
    ChordStart,
    ContextName,
    GrobName,
    SlurStart, SlurEnd,
    PhrasingSlurStart, PhrasingSlurEnd,
    Tie,
    BeamStart, BeamEnd,
    LigatureStart, LigatureEnd,
    Direction,
    Articulation,
) + command_items
    

# items that occur inside chords
music_chord_items = (
    ErrorInChord,
    ChordEnd,
) + music_items



class LilyPondParserGlobal(LilyPondParser):
    """Parses LilyPond from the toplevel of a file."""
    # TODO: implement assignments
    items = (
        Book,
        BookPart,
        Score,
        Markup, MarkupLines,
        Paper, Header, Layout,
    ) + toplevel_base_items + (
        Name,
        EqualSign,
    )


class ExpectOpenBracket(LilyPondParser):
    """Waits for an OpenBracket and then replaces the parser with the class set in the replace attribute.
    
    Subclass this to set the destination for the OpenBracket.
    
    """
    default = Error
    items = space_items + (
        OpenBracket,
    )
    def updateState(self, state, token):
        if isinstance(token, OpenBracket):
            state.replace(self.replace())
        

class ExpectOpenBrackedOrSimultaneous(LilyPondParser):
    """Waits for an OpenBracket or << and then replaces the parser with the class set in the replace attribute.
    
    Subclass this to set the destination for the OpenBracket.
    
    """
    default = Error
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(self.replace())
        

class LilyPondParserScore(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        Header, Layout, Midi, With,
    ) + toplevel_base_items


class LilyPondParserExpectScore(ExpectOpenBracket):
    replace = LilyPondParserScore
            

class LilyPondParserBook(LilyPondParser):
    """Parses the expression after \book {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines,
        BookPart,
        Score,
        Paper, Header, Layout,
    ) + toplevel_base_items



class LilyPondParserExpectBook(ExpectOpenBracket):
    replace = LilyPondParserBook


class LilyPondParserBookPart(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines,
        Score,
        Paper, Header, Layout,
    ) + toplevel_base_items


class LilyPondParserExpectBookPart(ExpectOpenBracket):
    replace = LilyPondParserBookPart


class LilyPondParserPaper(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = base_items + (
        CloseBracket,
        Markup, MarkupLines,
        PaperVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class LilyPondParserExpectPaper(ExpectOpenBracket):
    replace = LilyPondParserPaper


class LilyPondParserHeader(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines,
        HeaderVariable,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserExpectHeader(ExpectOpenBracket):
    replace = LilyPondParserHeader
        

class LilyPondParserLayout(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = base_items + (
        CloseBracket,
        LayoutContext,
        LayoutVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class LilyPondParserExpectLayout(ExpectOpenBracket):
    replace = LilyPondParserLayout
        

class LilyPondParserMidi(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = base_items + (
        CloseBracket,
        LayoutContext,
        LayoutVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class LilyPondParserExpectMidi(ExpectOpenBracket):
    replace = LilyPondParserMidi


class LilyPondParserWith(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserExpectWith(ExpectOpenBracket):
    replace = LilyPondParserWith
        

class LilyPondParserContext(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        BackSlashedContextName,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserExpectContext(ExpectOpenBracket):
    replace = LilyPondParserContext
        

class LilyPondParserMusic(LilyPondParser):
    """Parses LilyPond music expressions."""
    items = music_items
    

class LilyPondParserChord(LilyPondParserMusic):
    """LilyPond inside chords < >"""
    items = music_chord_items


class StringParser(Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class BlockCommentParser(Parser):
    default = Comment
    items = (
        BlockCommentSpace,
        BlockCommentEnd,
    )


class MarkupParser(Parser):
    items =  (
        MarkupScore,
        MarkupCommand,
        OpenBracketMarkup,
        CloseBracketMarkup,
        MarkupWord,
    ) + base_items


class RepeatParser(FallthroughParser):
    items = space_items + (
        RepeatSpecifier,
        RepeatStringSpecifier,
        RepeatCount,
    )


class DurationParser(FallthroughParser):
    items = space_items + (
        Dot,
    )
    def fallthrough(self, state):
        state.replace(DurationScalingParser())
        
        
class DurationScalingParser(DurationParser):
    items = space_items + (
        Scaling,
    )
    def fallthrough(self, state):
        state.leave()


class LilyPondParserOverride(LilyPondParser):
    argcount = 0
    items = (
        ContextName,
        DotSetOverride,
        GrobName,
        EqualSignSetOverride,
        Name,
        Markup, MarkupLines,
    ) + base_items
    

class LilyPondParserRevert(FallthroughParser):
    items = space_items + (
        ContextName,
        DotSetOverride,
        GrobName,
        Name,
        SchemeStart,
    )

    
class LilyPondParserSet(LilyPondParser):
    argcount = 0
    items = (
        ContextName,
        DotSetOverride,
        ContextProperty,
        EqualSignSetOverride,
        Name,
        Markup, MarkupLines,
    ) + base_items
    
    
class LilyPondParserUnset(FallthroughParser):
    items = space_items + (
        ContextName,
        DotSetOverride,
        ContextProperty,
        Name,
    )


class LilyPondParserNewContext(FallthroughParser):
    items = space_items + (
        ContextName,
        Name,
        EqualSign,
        StringQuotedStart,
    )


class LilyPondParserClef(FallthroughParser):
    argcount = 1
    items = space_items + (
        ClefSpecifier,
        StringQuotedStart,
    )


class ScriptAbbreviationParser(FallthroughParser):
    argcount = 1
    items = space_items + (
        ScriptAbbreviation,
    )


class InputModeParser(LilyPondParser):
    """Base class for parser for mode-changing music commands."""
    
    
class LilyPondParserExpectLyricMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
        SchemeStart,
        StringQuotedStart,
        Name,
    )
    
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(LilyPondParserLyricMode())
        

class LilyPondParserLyricMode(InputModeParser):
    """Parser for \\lyrics, \\lyricmode, \\addlyrics, etc."""
    items = base_items + (
        CloseBracket,
        CloseSimultaneous,
        OpenBracket,
        OpenSimultaneous,
        LyricHyphen,
        LyricExtender,
        LyricSkip,
        LyricTie,
        LyricText,
        Dynamic,
        Skip,
        DurationStart,
        Markup, MarkupLines,
    ) + command_items
    
    def updateState(self, state, token):
        if isinstance(token, (OpenSimultaneous, OpenBracket)):
            state.enter(LilyPondParserLyricMode())


class LilyPondParserExpectChordMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(LilyPondParserChordMode())
        

class LilyPondParserChordMode(InputModeParser, LilyPondParserMusic):
    """Parser for \\chords and \\chordmode."""
    pass # TODO: implement


class LilyPondParserExpectNoteMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(LilyPondParserNoteMode())
        

class LilyPondParserNoteMode(InputModeParser, LilyPondParserMusic):
    """Parser for \\notes and \\notemode. Same as Music itself."""


class LilyPondParserExpectDrumMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(LilyPondParserDrumMode())
        

class LilyPondParserDrumMode(InputModeParser, LilyPondParserMusic):
    """Parser for \\drums and \\drummode."""
    pass # TODO: implement


class LilyPondParserExpectFigureMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def updateState(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(LilyPondParserFigureMode())
        

class LilyPondParserFigureMode(InputModeParser, LilyPondParserMusic):
    """Parser for \\figures and \\figuremode."""
    pass # TODO: implement
    


