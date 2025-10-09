requirejs.config({
    shim: {
        jquery: {
            exports: "$"
        },
        cookie: {
            exports: "Cookies"
        },
        bootstrap: {
            deps: ["jquery"]
        },
    },
    baseUrl: "/static/simple_dashboard/js/app",
    paths: {
        app: '/static/simple_dashboard/js/app',
        material: "/static/simple_dashboard/js/vendor/material-components-web-11.0.0",
        jquery: "/static/simple_dashboard/js/vendor/jquery-3.4.0.min",
        cookie: "/static/simple_dashboard/js/vendor/js.cookie"
    }
});

const toLoad = ["material", "cookie", "jquery", "base"]

if (window.dashboadAdditionalModules) {
	toLoad.push(...window.dashboadAdditionalModules)
}

requirejs(toLoad, function(mdc, Cookies) {
	window.materialDesignComponents = mdc

	const doSearch = function(query) {
		const url = URL.parse(window.location.href)
		url.searchParams.set('limit', select.value)
		url.searchParams.set('offset', '0')
		url.searchParams.set('q', query)

		window.location.href = url.href
	}

	const searchField = mdc.textField.MDCTextField.attachTo(document.getElementById('topbar_search'));

	$('#topbar_search_field').on('keypress', function(eventObj) {
		if (eventObj.which == 13) {
			eventObj.preventDefault();

			doSearch(searchField.value)
		}
	})

	$('#topbar_search_icon').on('click', function(eventObj) {
		doSearch(searchField.value)
	})

	const select = mdc.select.MDCSelect.attachTo(document.querySelector('.mdc-select'));

	const url = URL.parse(window.location.href)

	if (url.searchParams.get('limit') !== null) {
		select.value = url.searchParams.get('limit')
	} else {
		select.value = '25'
	}

	if (url.searchParams.get('q') !== null) {
		searchField.value = url.searchParams.get('q')
	}

	select.listen('MDCSelect:change', () => {
		const url = URL.parse(window.location.href)
		url.searchParams.set('limit', select.value)
		window.location.href = url.href
	});

	const addParticipant = mdc.dialog.MDCDialog.attachTo(document.getElementById('add_participant_dialog'));

	const deleteParticipant = mdc.dialog.MDCDialog.attachTo(document.getElementById('confirm_delete_participant'));

	const addParticipantName = mdc.textField.MDCTextField.attachTo(document.getElementById('new_participant_name'));
	const addParticipantPhone = mdc.textField.MDCTextField.attachTo(document.getElementById('new_participant_phone'));
	const addParticipantEmail = mdc.textField.MDCTextField.attachTo(document.getElementById('new_participant_email'));

	$("#fab_add_participant").click(function(eventObj) {
		addParticipantName.value = '';

		$("#add-dialog-title").text('Add new participant')
		$('#dialog_update_study_button .mdc-button__label').text('Add')

		addParticipant.open();
	});

	$(".participant_url_button").click(function(eventObj) {
		const url = $(this).attr('data-url')

		window.location.href = url
	});


	$(".participant_update_button").click(function(eventObj) {
		$("#add-dialog-title").text('Update participant');

		const id = $(this).attr('data-edit-id')
		const name = $(this).attr('data-edit-name')
		const email = $(this).attr('data-edit-email')
		const phone = $(this).attr('data-edit-phone')
		const studies = $(this).attr('data-edit-studies').split(',')

		addParticipantName.value = name
		addParticipantEmail.value = email
		addParticipantPhone.value = phone

		$('.checkbox-study').prop('checked', false)

		studies.forEach(function(item) {
			$(`[id="checkbox-study-${item}"]`).prop('checked', true)
		});

		$('#update_participant_id').val(id)
		$('#dialog_update_participant_button .mdc-button__label').text('Update')

		addParticipant.open()
	});

	addParticipant.listen('MDCDialog:closed', function(event) {
		action = event.detail['action'];

		if (action == 'close') {

		} else if (action == 'create') {
			let studyIds = []

			$('.checkbox-study').each(function(item) {
				if ($(this).is(':checked')) {
					const id = $(this).attr('id').replace('checkbox-study-', '')

					studyIds.push(id)
				}
			})

			$.post('/research/dashboard/participant/update.json', {
				'name': addParticipantName.value,
				'email': addParticipantEmail.value,
				'phone': addParticipantPhone.value,
				'identifier': $('#update_participant_id').val(),
				'studies': studyIds.join(',')
			}, function(data) {
				if (data.message) {
					alert(data.message)
				}

				location.reload();
			});
		}
	});

	$(".participant_delete_button").click(function(eventObj) {
		eventObj.preventDefault()

		$("#delete_participant_name").text($(eventObj.target).data()["deleteName"]);
		$("#delete_participant_id").val($(eventObj.target).data()["deleteId"]);

		deleteParticipant.open()
	});

	deleteParticipant.listen('MDCDialog:closed', function(event) {
		action = event.detail['action'];

		if (action == 'close') {

		} else if (action == 'delete') {
			var deleteId = $("#delete_participant_id").val();

			$.post('/research/dashboard/participant/delete.json', {
				'identifier': deleteId
			}, function(data) {
				if (data.message) {
					alert(data.message)
				}

				location.reload();
			});
		}
	});

	$('.mdc-data-table__pagination-button').click(function(eventObj) {
		eventObj.preventDefault()

		const url = $(this).attr('data-url')

		window.location.href = url
	})

	$('.participant_menu_open').each(function(index, button) {
		$(button).parent().find('.mdc-menu').each(function(inelementIndex, element) {
			const menu = mdc.menu.MDCMenu.attachTo(element)

			menu.setFixedPosition(true)

			$(button).click(function (eventObj) {
				eventObj.preventDefault()

				menu.open = (menu.open === false)
			})
		})
    })

	mdc.dataTable.MDCDataTable.attachTo(document.getElementById('participants_table'));

	$('input[type="checkbox"]').off('change')

	$('input[type="checkbox"]').on('change', function(eventObj) {
		console.log('checkbox changed')
		console.log(eventObj)

		window.setTimeout(function() {
			const selectedPhones = []

			$('input:checked').each(function(index, checkbox) {
				$(checkbox).closest('.mdc-data-table__row').each(function(ansIndex, row) {
					const phone = $(row).attr('data-row-phone')

					if (phone !== undefined && phone !== '') {
						selectedPhones.push(phone)
					}
				})
			})

			window.updateSimpleMessagingBroadcastDestinations(selectedPhones)
		}, 250)
	})
});