from .basic_tests import BasicBaseTestCases
from .anything_tests import AnythingBaseTests
from .callback_tests import CallbackBaseTests
from .field_attribute_tests import FieldAttributeBaseTests
from .schema_tests import SchemaBaseTests
from .index_tests import IndexBaseTests

common_test_classes = [BasicBaseTestCases.BasicTests,
                        # BasicBaseTestCases.RefNameTests,
                        AnythingBaseTests.AnythingTests,
                        CallbackBaseTests.CallbackTests,
                        FieldAttributeBaseTests.FieldAttributeTests,
                        SchemaBaseTests.SchemaTests,
                        IndexBaseTests.IndexTests
                        ]