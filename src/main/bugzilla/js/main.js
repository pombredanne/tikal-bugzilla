// -- Tikal package
Tikal = {}
Tikal.Bugzilla = {}


 /**
 * Form package.
 */
Tikal.Bugzilla.FormUtil = function() {
    return {

		/**
		 * Get form element.
		 * @param obj - can be an id or the an instance.
		 */
		getForm: function(formName) {
			// Arguments validation.
			if (formName == null) {
				return false;
			}
			var form = document.forms[formName];
			if (form != null) {
				return form;
			}	
			return null;
		},

		/**
		 * Get form's input element.
		 * @param formName 
		 * @param inputName
		 */
		getInput: function(formName, inputName) {
			// Arguments validation.
			if (formName == null || inputName == null) {
				return false;
			}
			var form = this.getForm(formName);
			if (form != null) {
				return form.elements[inputName];
			}
			return null;
		}
	}
}();

 /**
 * Util package.
 */
Tikal.Bugzilla.Util = function() {
    return {

		/**
		 * Get an element.
		 * @param obj - can be an id or the an instance.
		 */
		getEl: function(obj) {
			var testObj = document.getElementById(obj);
			if (testObj != null) {
				// we've got an id.
				return testObj;
			} else {
				// we might have an object
				return (typeof obj == 'string' ? null : obj);
			}
		},

		/**
		 * InnerHTML - dom implementation.
		 * Use this function for setting text into HTML element.
		 *
		 * @param obj - id or element to be referenced.
		 * @param value to be set.
		 */
		setInnerHTML: function(obj, value) {
			if (obj == null || value == null) return;
			var textElt = document.createTextNode(value);
			var targetElt = this.getEl(obj);
			if (targetElt != null) {
			    this.getEl(obj).appendChild(textElt);
			}
		},

		/**
		 * InnerHTML - dom implementation.
		 * Use this function for adding a text to HTML element.
		 *
		 * @param obj - id or element to be referenced.
		 * @param value to be set.
		 */
		add2InnerHTML: function (obj, value) {
			if (obj == null || value == null) return;
			var targetElt = this.getEl(obj);
			if (targetElt != null) {
				value += (targetElt.firstChild.data != null ? targetElt.firstChild.data :"");
				var textElt = document.createTextNode(value);
			    targetElt.replaceChild(textElt, targetElt.firstChild);
			}
		}
	}
}();



// end of Tikal package.


/**
 *  Make sure that only one chekbox with the same id is checked.
 *  name - check box name.
 *  status - true for checked or else false.
 */
function checkBoxAll(name, status) {
	var checkboxObj = document.getElementsByTagName("input");
	if (checkboxObj != null) {
		var size = checkboxObj.length;
		if (size > 1) {
			for (i=0; i<size; i++) {
				if(checkboxObj[i].type == "checkbox" && checkboxObj[i].name == name) {
					checkboxObj[i].checked = status;
				}
			}
		}
	}
}

/**
 *  Make sure that only one chekbox with the same id is checked.
 *  obj - the pressed checkbox.
 */
function checkBoxValidation(obj, name) {
	var notifyObj = document.getElementsByTagName("input");
	var n=0;
	var result = obj.checked;
	if (notifyObj != null) {
		var size = notifyObj.length;
		if (size > 1) {
			for (i=0; i<size; i++) {
				if( notifyObj[i].type == "checkbox" && (getLevel(notifyObj[i].id) != getLevel(obj.id)) ) {
					notifyObj[i].checked = false;
					n++;
				}
			}
			if (n > 0){
				obj.checked = result;
			}

		}
	}
}

/**
 * get the row level number [foo_1 => 1]
 */
function getLevel(value) {
	if (value != null) {
		var valueStr = "_";
		var valuePos = value.lastIndexOf(valueStr);
		if (valuePos != -1) {
			levelPos = valuePos + valueStr.length;
			return value.substring(levelPos, levelPos + 1);
		}
	}
}

/**
 * setting the H tag size accoring to the browser.
 * FF has to get smaller value.
 */
function setHSize(displayName, hsize) {
	if (!is.ie) {
		document.write('<h'+ hsize +' style="margin:0">');
	} else {
		document.write('<h'+ (hsize+1) +' style="margin:0">');
	}
	document.write(displayName);
	if (!is.ie) {
		document.write('</h'+ hsize +'>');
	} else {
		document.write('</h'+ (hsize+1) +'>');
	}
}

/* **** Init Parameters ***** */
var defaultSelectWidth = 150;
var defaultLength = 18;
var defaultCharWidth = 7;

var defaultWindowWidth = 400;
var defaultWindowHeight = 295;
var childWin = null;
var elementId = "";
var selectedValues = "";
var separatorStr = ";";
var elementType = new Array();
var attributeNameGl = "";
var elementIdGl = "";
elementType[0] = "text";
elementType[1] = "select-one";
elementType[2] = "select-multiple";
elementType[3] = "hidden";
var elementValues;

function doAction(elementTypeVar,id,name,desc,url,aProperties){
        setElementId(id);

        /* select-multiple */
        if (elementTypeVar == elementType[2]){
                multiValueSelect(id,name,desc,url,aProperties);

        /* select-one */
        }else if (elementTypeVar == elementType[1]){
                multiValueSelect(id,name,desc,url,aProperties);

        /* text / hidden */
        }else if (elementTypeVar == elementType[0] || elementTypeVar == elementType[3]){
                selectedValues = document.getElementById(id).value + separatorStr;
                openMultiValueSelect(id,selectedValues,desc,url,aProperties);
        }


}

function multiValueSelect(id,name,desc,url,aProperties){

        selectedValues = "";
        var seletedIndexes = new Array();
	   	var obj = desc.elements[id];
	   	desc = desc.elements[id].innerHTML;

        for (i=0; i<obj.options.length;i++){
                if (obj.options[i].selected){
                        seletedIndexes[i]=i;
                        selectedValues += obj.options[i].value + separatorStr;
                }
        }
        openMultiValueSelect(id,selectedValues,desc,url,aProperties);

}

function setSelectedMultiBox(id,str){

        var selectedArray = new Array();
        var obj = document.getElementById(id);
        selectedArray = str.split(separatorStr);

        for (i=0; i<obj.options.length;i++){
                obj.options[i].selected = false;

                for (j=0; j<selectedArray.length;j++){
                        if (obj.options[i].value == selectedArray[j]){
                                obj.options[i].selected = true;
                        }
                }
        }
}

function setSelectedTextBox(id,str){

        var obj = document.getElementById(id);
        obj.value=str;
}

function setSelectedValues(id,value){
 	if (id != null) {
		var obj = document.getElementById(id);
		/* select-multiple */
		if (obj.type == elementType[2]){
			setSelectedMultiBox(id,value);

		/* select-one */
		}else if (obj.type == elementType[1]){
			setSelectedMultiBox(id,value);

		/* text / hidden */
		}else if (obj.type == elementType[0] || obj.type == elementType[3]){
			setSelectedTextBox(id,value);
		}
	}
}

function getElementId(){
        return elementId;
}

function setElementId(value){
        elementId = "";
        elementId = value;
}

function openWindow(url,param,properties,isReturn){
    /**
     *  Description:
     *      open a new window browser.
     *
     *  parameters:
     *           url: The view's name to be displayed at this window (JSP view).
     *         param: Used as Target parameter can be one of these values _parent, _search, _self, _top or specific element.
         *    properties: Window properties:

                                                         fullscreen = { yes | no | 1 | 0 } [no]
                                                         height = number
                                                         width = number
                                                         top = number
                                                         left=number
                                                         location = { yes | no | 1 | 0 } [yes]
                                                         menubar = { yes | no | 1 | 0 } [yes]
                                                         resizable = { yes | no | 1 | 0 } [yes]
                                                         scrollbars = { yes | no | 1 | 0 } [yes]
                                                         status = { yes | no | 1 | 0 } [yes]
                                                         titlebar = { yes | no | 1 | 0 } [yes]
                                                         toolbar = { yes | no | 1 | 0 } [yes]

                                                         properties syntax (Ok with netscape and IExplorer): [paramter=value,...]
    */

        // defaults
        if (properties==null) properties = 'width=400,height=200,top=100,left=150,resizable=no';
        if (isReturn==null) isReturn = false;

        if (isReturn){
			winObj = window.open(url,param,properties);
			winObj.focus();
            return winObj;
        }else{
				window.open(url,'test',properties);
        }

}

function openMultiValueSelect(elementId,attributeName,attributeDisplayName, url, aProperties) {

		if (url == null) {
	        url = 'multivaluewindow.html';
		}

		tempX = 100;
        tempY = 100;
        var propertiesMulti = "";
        var paramMulti = 'keepwindowopen'+rand();

		if (attributeName=='') {
			attributeName=attributeDisplayName;
		} else {
			attributeName= attributeName + '&attributeDisplayName=' + attributeDisplayName;
		}

        if (is.ie){

                elementValues=attributeName;
				attributeNameGl = attributeName;
				elementIdGl = elementId;
				if (aProperties == null) {
					propertiesMulti = 'height=500px,width=500px,status=1,resizable=1';
				} else {
					propertiesMulti = aProperties;
				}
                childWin  = openWindow(url,paramMulti,propertiesMulti,true);

        }else{
				attributeNameGl = attributeName;
				elementIdGl = elementId;
				if (aProperties == null) {
					propertiesMulti = 'height=500px,width=500px,status=1,resizable=1';
				} else {
					propertiesMulti = aProperties;
				}
                childWin  = openWindow(url,paramMulti,propertiesMulti,true);
		}

}

function LTrim(str){
        var whitespace = new String(" \t\n\r");
        var s = new String(str);
        if (whitespace.indexOf(s.charAt(0)) != -1) {
                var j=0, i = s.length;
                while (j < i && whitespace.indexOf(s.charAt(j)) != -1)
                        j++;
                s = s.substring(j, i);
        }

        return s;
}

function RTrim(str){
        var whitespace = new String(" \t\n\r");

        var s = new String(str);

        if (whitespace.indexOf(s.charAt(s.length-1)) != -1) {
                var i = s.length - 1;
                while (i >= 0 && whitespace.indexOf(s.charAt(i)) != -1)
                        i--;
                s = s.substring(0, i+1);
        }

        return s;
}

function Trim(str){
        return RTrim(LTrim(str));
}

function sortList(theList) {
        var text;
        var value;

        if (theList) {
                for (var i=0; i < (theList.options.length-1); i++) {
                        for (var j=i+1; j < theList.options.length; j++) {

                                if (theList.options[j].text < theList.options[i].text) {
                                        value = theList.options[i].value;
                                        text = theList.options[i].text;

                                        theList.options[i].value = theList.options[j].value;
                                        theList.options[i].text = theList.options[j].text;

                                        theList.options[j].value = value;
                                        theList.options[j].text = text;
                                }

                        }
                }
        }
}


function pointOnStr(theList,str) {
        var tempValue;
		var optionsLength = theList.options.length;

        if (str != "") {

              for (var j = 0;  j < theList.options.length; j++) {
                        theList.options[j].selected = false;
                }

                for (var i = 0;  i < theList.options.length; i++) {
                        tempValue = theList.options[i].text;
                        if ( (tempValue.toLowerCase().charAt(0) == str.toLowerCase().charAt(0)) &&
                                 (tempValue.toLowerCase().indexOf(str.toLowerCase()) != -1) ) {

							if(i+6<optionsLength && optionsLength>7){
                                theList.options[i+6].selected = true;
								theList.options[i].selected = true;
                                theList.options[i+6].selected = false;
							}	else if (optionsLength>7) {
								theList.options[optionsLength-1].selected = true;
								theList.options[i].selected = true;
                                theList.options[optionsLength-1].selected = false;
							} else{
								theList.options[i].selected = true;
							}
								return;
                        }
                }
        }
        else {
                theList.options[0].selected = true;
        }
}


function insertState(theList, theOption) {
        theList.options.length = theList.options.length + 1;

        for (var i = theList.options.length-2; i >= 0; i--) {
                if (theOption.text.toUpperCase() > theList.options[i].text.toUpperCase()) {
                        theList.options[i+1].value= theOption.value;
                        theList.options[i+1].text= theOption.text;
                        return 0;
                }
                else {
                        theList.options[i+1].value=theList.options[i].value ;
                        theList.options[i+1].text=theList.options[i].text ;
                }
        }
        theList.options[0].value = theOption.value;
        theList.options[0].text = theOption.text;
}


function moveStates(sourceList, targetList) {
        for (var i = sourceList.options.length-1; i >= 0; i--) {
                if (sourceList.options[i].selected) {
                        insertState(targetList,sourceList.options[i]);
                        sourceList.options[i] = null;
                }
        }
}

function moveAllStates(sourceList, targetList) {
        for (var i = sourceList.options.length-1; i >= 0; i--) {
               insertState(targetList,sourceList.options[i]);
               sourceList.options[i] = null;
        }
}

function moveUp(theList) {
        if (theList.options.length > 0 && theList.selectedIndex > 0) {
                var i = theList.selectedIndex;
                var selectValue = theList[theList.selectedIndex].value;
                var selectText = theList[theList.selectedIndex].text;
                theList.options[i].value = theList.options[i-1].value;
                theList.options[i].text = theList.options[i-1].text;
                theList.options[i-1].value = selectValue;
                theList.options[i-1].text = selectText;
                theList.options[i-1].selected=true;
        }
}


function moveDown(theList) {
        if (theList.options.length > 0 &&
                theList.selectedIndex < theList.options.length-1 &&
                theList.selectedIndex >= 0 ) {

                var i = theList.selectedIndex;
                var selectValue = theList[theList.selectedIndex].value;
                var selectText = theList[theList.selectedIndex].text;
                theList.options[i].value = theList.options[i+1].value;
                theList.options[i].text = theList.options[i+1].text;
                theList.options[i+1].value = selectValue;
                theList.options[i+1].text = selectText;
                theList.options[i+1].selected=true;
        }
}



function updateOpener(theList,elementId) {
        var textStr = "";
        var valueStr = "";

        for (var i=0; i < theList.options.length; i++) {
                textStr += theList.options[i].text;
                if ((theList.options.length - i) > 1) textStr += ";";
                valueStr += theList.options[i].value;
                if ((theList.options.length - i) > 1) valueStr += ";";
        }

        if (is.ie){

			if (elementId != null) {
	                window.opener.setSelectedValues(elementId,valueStr);
				}

		}else{
				if (elementId != null) {
	                window.opener.setSelectedValues(elementId,valueStr);
				}
        }

        window.close();

}


function resizeElements(sourceList, targetList, theTextBox) {
        var maxLength = 0;
        var resizeOffset;
        var maxWidth = defaultSelectWidth;

        window.resizeTo(defaultWindowWidth,defaultWindowHeight);

        if (sourceList && targetList) {
                for (var i = 0;  i < sourceList.options.length; i++) {
                        if (parseInt(sourceList.options[i].text.length) > parseInt(maxLength)) {
                                maxLength = sourceList.options[i].text.length;
                        }
                }

                for (var i = 0;  i < targetList.options.length; i++) {
                        if (parseInt(targetList.options[i].text.length) > parseInt(maxLength)) {
                                maxLength = targetList.options[i].text.length;
                        }
                }

                if (parseInt(maxLength) > parseInt(defaultLength)) {
                        resizeOffset = ((parseInt(maxLength) - parseInt(defaultLength)) * defaultCharWidth) + 1;
                        maxWidth += resizeOffset;
                }

                sourceList.style.width = maxWidth;
                targetList.style.width = maxWidth;
                theTextBox.style.width = maxWidth;
                window.resizeBy(resizeOffset*2,0);
        }
}


function checkChildWindowOpen(){

	if(childWin != null){

		if(childWin.document != null){
			if (childWin) {
				childWin.focus();
			}
		}
	}
}

function setChildWindowToNull(){
}

function rand() {
	now=new Date();
	num=(now.getSeconds())%100;
	num=num+1;
	return num;
}

function loadValuesFromInput(sourceList, targetList,elementValues) {
        var inputValue = null;
        if (is.ie){
			 inputValue = elementValues;
        }else{
             inputValue = localAttribute;
        }

	  var fromIndex = 0;
        var toIndex = 0;
        inputValue;

		while ((toIndex = inputValue.indexOf(";",fromIndex)) != -1) {
                for (var i = sourceList.options.length-1; i >= 0; i--) {
                        if (sourceList.options[i].value == Trim(inputValue.substring(fromIndex,toIndex))) {
                                targetList.options.length = targetList.options.length + 1;
                                targetList.options[targetList.options.length - 1].value = sourceList.options[i].value;
                                targetList.options[targetList.options.length - 1].text = sourceList.options[i].text;
                                sourceList.options[i] = null;
                        }
                }
                fromIndex = toIndex + 1;
        }
}

function loadValues(sourceList,elementValues) {
        var inputValue = null;
        if (is.ie){
			 inputValue = elementValues;
        }else{
             inputValue = localAttribute;
        }
}

function isDateFormat(dateToValidate){

	var re_date = new RegExp("^[0-9]{4}-[0-9]{2}-[0-9]{2}$");

        if (dateToValidate != null && dateToValidate != ""){
                if(re_date.test(dateToValidate)){
                        return true;
                }
	}
	return false;
}

function isRelativeDate(dateToValidate){

	var re_date = new RegExp("^[0-9](d|w|m|y)$");

        if (dateToValidate != null && dateToValidate != ""){
		if (dateToValidate == "Now" || dateToValidate == "now")
			return true;

                if(re_date.test(dateToValidate)){
                        return true;
                }
	}
	return false;
}

function validateDate(dateToValidate){

	var re_date = new RegExp("^[0-9]{4}-[0-9]{2}-[0-9]{2}$");

	if (dateToValidate != null && dateToValidate != ""){
		if(!re_date.test(dateToValidate)){
			return false;
		}

		var arr = dateToValidate.split("-");
		var year = parseInt(arr[0],10);
		var month = parseInt(arr[1],10);
		var date = parseInt(arr[2],10);

		// check year
		if (year < 2000 || year > 2100) { return false; }

		// check month
		if (month < 1 ||month > 12) { return false; }

		if (date < 1) { return false; }

		// check date for month
		if ((month==1)||(month==3)||(month==5)||(month==7)||(month==8)||(month==9)||(month==12)) {
			if (date > 31) { return false; }
		}
		if ((month==4)||(month==6)||(month==9)||(month==11)) {
			if (date > 30) { return false; }
		}
		if (month==2) {
			// Check for leap year
			if ( ( (year%4==0)&&(year%100 != 0) ) || (year%400==0) ) { // leap year
				if (date > 29) { return false; }
			}
			else {
				if (date > 28) { return false; }
			}
		}
	}
	return true;
}

// -- sort window impl
function openSortWindow(url, aProperties) {

		if (url == null) {
	        url = 'sortwindow.html';
		}

		if (aProperties == null) {
			propertiesMulti = 'height=270px,width=200px,status=0,resizable=1';
		} else {
			propertiesMulti = aProperties;
		}

		keepAlive = 'sort';
		childWin  = openWindow(url,keepAlive,propertiesMulti,true);

}

function move(index,to,form) {
	var list = form;
	var total = list.options.length-1;
	if (index == -1) return false;
	if (to == +1 && index == total) return false;
	if (to == -1 && index == 0) return false;
	var items = new Array;
	var values = new Array;
	for (i = total; i >= 0; i--) {
		items[i] = list.options[i].text;
		values[i] = list.options[i].value;
	}
	for (i = total; i >= 0; i--) {
		if (index == i) {
			list.options[i + to] = new Option(items[i],values[i],0,1);
			list.options[i] = new Option(items[i + to], values[i+ to]);
			i--;
		} else {
			list.options[i] = new Option(items[i], values[i]);
	    }
	}
}
function sortClick(){
	openSortWindow();
}
function isListEmpty(object) {
	if(object != null && object.length > 0) {
		return false;
	}
	return true;
}
function getSortList(object) {
	var result = null;
	if (!isListEmpty(object)) {
		result = object.split(",");
	}
	return result;
}
function updateSortOpener(sortIDs) {
	var value = sortIDs.options;
	if (!isListEmpty(value)) {
		var result = "";
		for (valueIdx=0; valueIdx<value.length; valueIdx++) {
			result += value[valueIdx].value;
			if (valueIdx < value.length-1) {
				result += ",";
			}
		}
		window.opener.document.forms[1].sorted_sub_list.value=result;
		window.opener.document.forms[1].action.value="sort";
		window.opener.document.forms[1].submit();
	}
}

/**
*  Description:
*      Replace a token in a string.
*
*  parameters:
*                      str:             string to be processed.
*                      findTok:  token to be found and removed.
*                      replaceTok:  token to be inserted.
*		       isOne: indicator if replcae obly one token of the substr
*
*  return: new parsed String.
*/

function replaceString(str, findTok, replaceTok, isOne) {

        pos = str.indexOf(findTok);
        valueRet = "";
        if (pos == -1) {
            return str;
        }
        valueRet += str.substring(0,pos) + replaceTok;
        if (!isOne && ( pos + findTok.length < str.length)) {
                valueRet += replaceString(str.substring(pos + findTok.length, str.length), findTok, replaceTok);
        } else {
		valueRet += str.substring(pos + findTok.length, str.length)
	}

        return valueRet;
}

function loadStyleClass() {
        if (is.ie) {
        	document.getElementById('menu-firefox').disabled = true;
        	document.getElementById('menu-ie').disabled = false;
        } else {
        	document.getElementById('menu-ie').disabled = true;
        	document.getElementById('menu-firefox').disabled = false;
        }

}

function setCancelBubble(evt, isCancel) {
		var e = window.event ? window.event : evt;
		if (isCancel == null) {
			isCancel = true;
		}
		e.cancelBubble = isCancel;
		/*if (is.ie) {
			e.cancelBubble = isCancel;
		} else {
			event.cancelBubble = isCancel;
			event.returnValue = false;

		}*/
}


/**
 *	switch between groups state [hide / show]
 *
 *  obj               - the on-clicking object.
 *  hideShowMe        - the object to be worked on.
 *  direction         - can be open or close.
 *  borderColor       - the border coor of the table.
 *  addOnEval         - add-on functionality by using eval()
 *  loop              - size of the elements (make sure the format is: [hideShowMe + _ + counter])
 *  headerWidthCheck  - make sure the header width will remain as is on display:none format [headerWidthCheck + _ + counter].
 */
function switchMaxMinImages(obj, hideShowMe, borderColor, addOnEval, loop, headerWidthCheck, direction) {
	var headerWidthCheck = (headerWidthCheck != null? headerWidthCheck : null);
	var hideShowMeConst = hideShowMe;
	var openConstant = "up";
	var closeConstant = "down";
	borderColor = (borderColor == null ? '#4c5576' : borderColor);
	var srcImg = obj.src;
	var max_minPosImg = srcImg.indexOf("arrow-down.gif");
	var min_maxPosImg = srcImg.indexOf("arrow-up.gif");
	if (direction == null) {
		direction = (srcImg.indexOf("arrow-up.gif") != -1 ? closeConstant : openConstant);
	}
	var prefix = srcImg.substring(0, (max_minPosImg != -1 ? max_minPosImg : min_maxPosImg));
	var suffix = srcImg.substring((max_minPosImg != -1 ? max_minPosImg : min_maxPosImg), srcImg.length);

	// check that the header size will not be change.
	if (headerWidthCheck != null) {
		i=1;
		while (document.getElementById(headerWidthCheck + "_" + i) != null && document.getElementById(headerWidthCheck + "_" + i).width == "") {
			headerWidthCheckObj = document.getElementById(headerWidthCheck + "_" + i)
			headerWidthCheckObj.width = headerWidthCheckObj.offsetWidth;
			i++;
		}
	}

	if (loop == null || loop == 0) {
		loop = 1;
	}
	for (i=1; i<=loop; i++) {
		if (loop > 1) {
			hideShowMe = hideShowMeConst + "_" +  i;
		}
		var hideShowMeObj = document.getElementById(hideShowMe);
		hideShowMeObj.style.display = (direction == openConstant ? 'none' : '');
		if (loop == 1) {
			//hideShowMeObj.style.borderBottom = (direction == openConstant ? '0px solid transparent' : '1px solid' + borderColor);
		}
	}
	obj.src = prefix + (srcImg.indexOf("anim-") == -1 ? "anim-arrow-" + (direction == openConstant ? "up" : "down" ) + ".gif" : "arrow-" + (direction == openConstant ? "up" : "down" ) + ".gif");
	obj.title = (direction == openConstant ? "Maximize" : "Restore Down" );
	if (addOnEval != null) {
		eval(addOnEval);
	}
}

function switchMaxMinImagesDirection(obj, hideShowMe,direction, borderColor, addOnEval, loop, headerWidthCheck) {
	switchMaxMinImages(obj, hideShowMe, borderColor, addOnEval, loop, headerWidthCheck, direction);
}

function switchMaxMinSubtasks(objid, hideShowMe, borderColor, addOnEval, loop, headerWidthCheck, direction){
	switchMaxMinImages(document.getElementById(objid), hideShowMe, borderColor, addOnEval, loop, headerWidthCheck, direction);
	if (document.getElementById("msubtasks").innerHTML == "Expand All"){
		Tikal.Bugzilla.Util.setInnerHTML("msubtasks", "Collapse All");
	} else {
		Tikal.Bugzilla.Util.setInnerHTML("msubtasks", "Expand All");
	}
}


/**
 *	Expand/Collapse all bug's comments.
 *
 *  commentSize - total comment size.
 *  stateInit = set 1 for Expand init or else 2 for Collapse init.
 */
function allCommentAction(commentSize, stateInit, expandId, imgId, prefixId, imgIdx) {
	var state1 = "Expand All";
	var state2 = "Collapse All";
	var expandObj = document.getElementById(expandId == null ? 'comments_expand' : expandId);
	imgId = (imgId == null ? "img_comment_" : imgId);
	prefixId = (prefixId == null ? "comment_" : prefixId);
	if (stateInit != null) {
		if (stateInit == 1) {
			Tikal.Bugzilla.Util.setInnerHTML(expandObj, state1);
		} else if (stateInit == 2){
			Tikal.Bugzilla.Util.setInnerHTML(expandObj, state2);
		}
	}
	if (expandObj.innerHTML == state1) {
		Tikal.Bugzilla.Util.setInnerHTML(expandObj, state2);
		minimizeAction(commentSize, 'down', imgId, prefixId, imgIdx)
	} else {
		Tikal.Bugzilla.Util.setInnerHTML(expandObj, state1);
		minimizeAction(commentSize, 'up', imgId, prefixId, imgIdx)
	}
}

function minimizeAction(commentSize, direction, imgId, prefixId, imgIdx) {
	for (z=0; z<commentSize;z++) {
		switchMaxMinImagesDirection(document.getElementById(imgId + (imgIdx != null ? imgIdx : z)), prefixId + z, direction);
	}
}





/* ********* panes (browse) ******** */
	/**
	 *  Main chart bar drawing function
	 *
	 *  In case of inner label drawing use the following template:
	 *	<td>
	 *		<table id="bar-1" cellpadding=0 cellspacing=0>
	 *			<tr>
	 *				<TD class="bar"><div class="chart_label"></div></TD>
	 *			</tr>
	 *		</table>
	 *	</td>
	 *
	 *  In case of outer label use the following template:
     *  <TD id="bar-1" class="bar">&nbsp;</TD>
	 *
	 *	In case of stack bar use this template:
	 *	<td>
	 *		<table cellpadding=0 cellspacing=0>
	 *		<tr>
	 * 			<td>
	 *				<table id="bar-1" cellpadding=0 cellspacing=0>
	 *					<tr>
	 *						<TD  class="bar" ><div class="chart_label" ></div></TD>
	 *					</tr>
	 *				</table>
	 *			</td>
	 *			<td>
	 *				<table id="bar-2" cellpadding=0 cellspacing=0>
	 *					<tr>
	 *						<TD  class="bar" ><div class="chart_label" ></div></TD>
	 *					</tr>
	 *				</table>
	 *			</td>
	 *		</tr>
	 *		</table>
	 *	</td>
     *
	 *
	 *	objName		- the bar object.
	 *	length		- the bar length to be draw.
	 *  value		- value to be displayed.
	 *  aColor		- fill the bar with this color.
	 *  isFloating	- if true the displayed value will be inner or else outer.
     */
	function drawBar(objName, length, value, aColor, isFloating){
		if (objName != null) {
			if (isFloating == null) {
				isFloating = true;
			}
			obj = document.getElementById(objName);
			if (obj != null) {
				if (aColor == null) {
					aColor = '#4C5576';
				}
				if (!isFloating) {
					obj.style.borderLeft= length + 'px solid ' + aColor;
				} else {
					obj.style.width= length;
				}
				if (value != null && value > 0) {
					if (isFloating) {
						obj.style.backgroundColor= aColor;
						//obj.style.borderTop='2px solid #b0b0b0';
						//obj.style.borderBottom='2px solid #b0b0b0';
						//obj.style.borderTop='2px solid #ea9d41';
						//obj.style.borderBottom='2px solid #ea9d41';
						// display inner bar text
						setFloatingBarLabel(obj.childNodes, value, '#4C5576');
					} else {
						// display outer bar text
						Tikal.Bugzilla.Util.setInnerHTML(obj, value);
						obj.style.color= "#ea9d41";
						obj.size = "8px";
					}
				} else {
					//obj.style.borderRight= '2px solid #b0b0b0';
					obj.style.display='none';
				}
			}
		}
	}

	function drawBarDark(objName, length, value){
		drawBar(objName, length, value, '#e77d00');
	}

	function drawBarOutline(objName, length, value){
		drawBar(objName, length, value, '#4C5576', false);
	}

	function drawBarLight(objName, length, value){
		drawBar(objName, length, value, '#b0b0b0');
	}

	/*
	 * Setting a label within the bar, make sure that
	 * <div class="chart_label" ></div> is inside the bar table
	 * or else the label will not be displayed.
	 *
	 * aObj		- the inner object (DIV) to be set.
	 * value	- the label value.
	 * bgcolor	- the color of the label;
	 */
	function setFloatingBarLabel(aObj, value, bgcolor) {
		var objLbl = getNextNodeByTagName(aObj, "DIV");
		if (objLbl != null) {
			Tikal.Bugzilla.Util.setInnerHTML(objLbl, value);
			if (bgcolor == null) {
				bgcolor="#000000"
			}
		}
	}

	/*
	 * Calc the total width of a given str.
	 *
	 * str		  - the given string.
	 * digitWidth - set the char width [optional]
	 */
	function getLblSizeBydigits(str, digitWidth) {
		if (str != null) {
			if (digitWidth == null) {
				digitWidth = 8;
			}
			var size = str.length;
			return size*digitWidth;
		}
	}

	/*
	 * set the max chart width.
	 */
	function setChartByTop(name, width) {
		if (name != null) {
			obj = document.getElementById(name);
			if (obj != null) {
				obj.style.width = width;
			}
		}
	}

	/**
	 * Calc the bars width percentage. The anchor is the top
	 * bar length out of all. It means that in case of one bar
	 * use a dummy bar for maximum length.
	 */
	function calcBarChart(categories, realWidth, objName) {
		result = new Array();
		if (categories != null) {
			size = categories.length
			for (i=0; i<size; i++) {
				if (categories[i] > top) {
					top = categories[i];
				}
			}

			if (realWidth != null) {
				top = (top/realWidth) * 100;
			}
			for (i=0; i<size; i++) {
				result[i] = ( categories[i] / top ) * 100;
			}
		}
		return result;
	}

	/**
	 *	Detect the keyboard 'Enter' event and eval a given code.
     *
	 *  evalAction  - the code to be execute.
	 *  e			- event.
	 */
	function onEnterKey(evalAction, e) {
		 var key;

		 if(window.event) {
			key = window.event.keyCode;	//IE
		 } else {
			key = e.which;		//firefox
		 }

		 if(key == 13) {
			eval(evalAction);
		 }

		 return false;
	}

	/**
	 * Recursion for getting an hierarchic element as javascript object.
	 * It will look for the first one and then stop.
	 *
	 * nodeArray	- an array elements.
	 * tagname		- the tag element name (DIV, TD etc...)

	function getNextNodeByTagName(nodeArray, tagname) {
		var result = null;
		for (var z = 0; z < nodeArray.length; z++) {
			if (nodeArray[z].childNodes) {
				result = getNextNodeByTagName(nodeArray[z].childNodes, tagname);
				if (nodeArray[z].tagName == tagname) {
					result = nodeArray[z];
				}
			}
		}

		return result;
	} */

   /**
	* Recursion for getting an hierarchic element as javascript object.
	* It will look for the first one and then stop.
	*
	*	nodeArray	- an array elements.
	*	tagname		- the tag element name (DIV, TD etc...)
	*
	*	Note: FF (FireFox) is taking into account the TEXT_NODE while
	*   IE is not, thus we have to ignore all types except 1 (ELEMENT_NODE)
	*
	*   nodeType property:
	*	1  	ELEMENT_NODE
	*	2 	ATTRIBUTE_NODE
	*	3 	TEXT_NODE
	*	4 	CDATA_SECTION_NODE
	*	5 	ENTITY_REFERENCE_NODE
	*	6 	ENTITY_NODE
	*	7 	PROCESSING_INSTRUCTION_NODE
	*	8 	COMMENT_NODE
	*	9 	DOCUMENT_NODE
	*	10 	DOCUMENT_TYPE_NODE
	*	11 	DOCUMENT_FRAGMENT_NODE
	*	12	NOTATION_NODE
	*/
	function getNextNodeByTagName(nodeArray, tagname) {
		var result = null;
		for (var z = 0; z < nodeArray.length; z++) {
			if (nodeArray[z].childNodes) {
				if (nodeArray[z].nodeType == 1) {
					result = getNextNodeByTagName(nodeArray[z].childNodes, tagname);
					if (nodeArray[z].tagName == tagname) {
						result = nodeArray[z];
					}
				}
			}
		}

		return result;
	}



