#!/usr/bin/perl
use strict;

my $line;
my $input = shift; # a line with the format "arg1=value1;arg2=value2
my @assignments = split(';', $input);
my %D;

# parse the input assignments
foreach $a (@assignments) {
    my ($key, $value) = split('=', $a);
    $key = clean($key);
    $value = clean($value);
    $D{$key} = $value;
}

# substitute variables
while ($line = <>) {
    foreach my $k (keys %D) {
      my $v = $D{$k};
      $line =~ s!{$k}!$v!g;
    }
    print $line;
}

# strip trailing whitespace from start or end.
sub clean {
    my $a = shift;
    $a =~ s/^\s*//;
    $a =~ s/\s*$//;
    return $a;
}
