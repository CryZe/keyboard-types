import re
import requests

def handle_enum_entries(text, file):
    display = []
    for match in re.findall(r"id=\".*?\">\"(.*?)\"</code>\n.*<td>(((.*?)\n)+?)\s+(<tr>|</table>)", text):
        # Skip F keys here
        if re.match("^F\d+$", match[0]):
            continue
        doc = re.sub(r"[ \t][ \t]+", "\n", match[1])
        doc = re.sub(r"<a .*?>(.*?)</a>", "\\1", doc)
        for line in doc.split('\n'):
            line = line.strip()
            if not line:
                continue
            print("    /// {}".format(line), file=file)
        display.append(match[0])
        print("    {},".format(match[0]), file=file)
    return display

def print_display_entries(display, file):
    for key in display:
        print("            {0} => f.write_str(\"{0}\"),".format(key), file=file)

def print_from_str_entries(display, file):
    for key in display:
        print("            \"{0}\" => Ok({0}),".format(key), file=file)


def add_f_keys(display, file, max_f_key, doc_comment):
    for index in range(1, max_f_key + 1):
        print("    ///", doc_comment.format(index), file=file)
        print("    F{},".format(index), file=file)
        display.append("F{}".format(index))

def convert_key(text, file):
    print("""
// AUTO GENERATED CODE - DO NOT EDIT

use std::fmt::{self, Display};
use std::str::FromStr;
use std::error::Error;

/// Key represents the meaning of a keypress.
///
/// Specification:
/// <https://w3c.github.io/uievents-key/>
#[non_exhaustive]
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
pub enum Key {
    /// A key string that corresponds to the character typed by the user,
    /// taking into account the user’s current locale setting, modifier state,
    /// and any system-level keyboard mapping overrides that are in effect.
    Character(String),
    """, file=file)
    display = handle_enum_entries(text, file)
    add_f_keys(display, file, 35, "The F{0} key, a general purpose function key, as index {0}.")
    print("}", file=file)

    print("""

impl Display for Key {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        use self::Key::*;
        match *self {
            Character(ref s) => write!(f, "{}", s),
    """, file=file)
    print_display_entries(display, file)
    print("""
        }
    }
}

impl FromStr for Key {
    type Err = UnrecognizedKeyError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        use Key::*;
        match s {
            s if is_key_string(s) => Ok(Character(s.to_string())),""", file=file)
    print_from_str_entries(display, file)
    print("""
            _ => Err(UnrecognizedKeyError),
        }
    }
}

/// Parse from string error, returned when string does not match to any Key variant.
#[derive(Clone, Debug)]
pub struct UnrecognizedKeyError;

impl fmt::Display for UnrecognizedKeyError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Unrecognized key")
    }
}

impl Error for UnrecognizedKeyError {}

/// Check if string can be used as a `Key::Character` _keystring_.
///
/// This check is simple and is meant to prevents common mistakes like mistyped keynames
/// (e.g. `Ennter`) from being recognized as characters.
fn is_key_string(s: &str) -> bool {
    s.chars().all(|c| !c.is_control()) && s.chars().skip(1).all(|c| !c.is_ascii())
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_is_key_string() {
        assert!(is_key_string("A"));
        assert!(!is_key_string("AA"));
        assert!(!is_key_string("\t"));
    }
}
    """, file=file)

def convert_code(text, file):
    print("""
// AUTO GENERATED CODE - DO NOT EDIT

use std::fmt::{self, Display};

/// Code is the physical position of a key.
///
/// The names are based on the US keyboard. If the key
/// is not present on US keyboards a name from another
/// layout is used.
///
/// Specification:
/// <https://w3c.github.io/uievents-code/>
#[non_exhaustive]
#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
pub enum Code {""", file=file)
    display = handle_enum_entries(text, file)
    add_f_keys(display, file, 35, "<code class=\"keycap\">F{0}</code>")
    print("}", file=file)

    print("""

impl Display for Code {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        use self::Code::*;
        match *self {
    """, file=file)
    print_display_entries(display, file)
    print("""
        }
    }
} 

    """, file=file)

if __name__ == '__main__':
    input = requests.get('https://w3c.github.io/uievents-key/').text
    with open('src/key.rs', 'w') as output:
        convert_key(input, output)
    input = requests.get('https://w3c.github.io/uievents-code/').text
    with open('src/code.rs', 'w') as output:
        convert_code(input, output)
