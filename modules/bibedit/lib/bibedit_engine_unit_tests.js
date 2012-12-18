ValueContainsSubfieldsTest = TestCase("ValueContainsSubfieldsTest");

ValueContainsSubfieldsTest.prototype.testContainsSubfield = function() {
	var value = "This is a test$$aAnd some subfield content";

	assertEquals(true, valueContainsSubfields(value));
};