$(function() {
	function ItemsSelector ($el) {
		this.init($el);
	}
	
	ItemsSelector.prototype = {
		init: function ($el)
		{
			var id = $el.attr("id"),
				sId = id && id != "" ? id : "item-selector-i-" + ItemsSelector.counter,
				inputId = sId.replace("items-selector_","") ;
			this.Actors = {
				itemsSelectorId: sId,
				listFilterCssClass: "find",
				selectedInputId: inputId
			};
			this._createFilter();
			this._generateLists();
			$("#" + this.Actors.itemsSelectorId).append(this.Actors.input);
		},
		
		_generateLists: function ()
		{
			var self = this,
				lists = $("#" + this.Actors.itemsSelectorId)
				.find("ul")
				.sortable({
					connectWith: ".connectedSortable"
				})
				.disableSelection()
				.bind("sortupdate", {context: this}, this.updateField)
				.bind("sortreceive", {context: this}, this.onItemMoved)
				.bind("click", {context: this}, this.onItemClick);
		},
		
		_createFilter: function ()
		{
			$("#" + this.Actors.itemsSelectorId).find("." + this.Actors.listFilterCssClass)
				.bind("keyup", {context: this}, this.handleKeys);
		},
		
		handleKeys: function (ev)
		{
			var self = ev.data.context,
				el = $(ev.target),
				sSearchValue = el.val() || "",
				leftList = $("#" + self.Actors.itemsSelectorId).find(".list.left"),
				items = leftList.find("li"),
				hasResult = true;
			if (ev.keyCode == 27) {
				sSearchValue = "";
				el.val("");
			}
			self.findItems(items, sSearchValue);
			if (sSearchValue == "")
				hasResult = false;
			leftList.toggleClass("filtered", hasResult);
		},
		
		findItems: function (items, sSearchValue)
		{
			for (var item, i = 0; i < items.length; i++) {
				item = items.eq(i);
				if (item.text().toLowerCase().indexOf(sSearchValue.toLowerCase()) == 0) {
					item.show();
				} else {
					item.hide();
				}
			}
		},
		
		onItemMoved: function (ev, ui) {
			ev.data.context.updateField();
		},
		
		onItemClick: function (ev) {
			ev.data.context.handleItem(ev.target);
		},
		
		getList: function (el) {
			if (el.hasClass("right"))
				return "left";
			return "right";
		},
		
		handleItem: function (element) {
			var el = $(element);
			if (el.hasClass("ui-state-default")) {
				var o = el.parents("div.list"),
					list = this.getList(o),
					itemId = el.attr("id");
				if (list == "right"){
					el.attr("id", itemId + "_sel");
				} else {
					el.attr("id", itemId.replace("_sel", ""));
				}
				$("#" + this.Actors.itemsSelectorId).find("." + list + " ul").append(el);
				this.updateField();
			}
		},
		
		updateField: function (ev) {
			var self = ev ? ev.data.context : this,
				$this = $("#" + self.Actors.selectedInputId),
				items = $("#" + self.Actors.itemsSelectorId).find(".right li"),
				values = [];
			for (var i = 0; i < items.length; i++) {
				values[values.length] = items.eq(i).attr("title");
			}
			$("#" + self.Actors.selectedInputId).val(values.join(","));
			$this.trigger(self.Actors.selectedInputId + "-change");
		},
		
		subscribe: function (func)
		{
			if (func) {
				var id = this.Actors.itemsSelectorId;
				$("#" + id).bind("changed-" + id, func);
			}
		}
	};
	
	ItemsSelector.instances = {};
	ItemsSelector.counter = 0;
	/**
	 *	initiates each items-selector element
	 */
	ItemsSelector.create = function() {
		var items = $(".items-selector");
		for (var i = 0; i < items.length; i++) {
			ItemsSelector.instances["is-" + i] = new ItemsSelector(items.eq(i));
			ItemsSelector.counter++;
		}
	}

	/**
	 *	@param	{array}
	 *	Add more suffixes to this array in order to generate item selector for each.
	 *	Suffixes must be unique
	 *	This suffix will be appended to the filter-id, wrapper-id
	 *	hidden input-id will be the same as the suffix
	 */
	ItemsSelector.create();
});