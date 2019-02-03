import React, {Component} from 'react';
import 'whatwg-fetch';
import cookie from 'react-cookies';

class SelectRes extends Component {
	constructor(props) {
		super(props);
		this.state = {date: '', num_guests: ''};
		this.handleChange = this.handleChange.bind(this);
		this.handleSubmit = this.handleSubmit.bind(this);
	}
	requestReservation() {
		const endpoint = '/reservation/request/';
		const csrfToken = cookie.load('csrftocken')
		console.log(`csrfToken = ${csrfToken}`);
		const lookupOptions = {
			method: 'POST',
			headers: {
				'X-CSRFToken': csrfToken,
			},
			body: JSON.stringify([this.state.date, this.state.num_guests]),
			credentials: 'include',
		}
		fetch(endpoint, lookupOptions).then(response => console.log(response));
	}
	handleChange(event) {
		const value = {[event.target.name]: event.target.value}
		console.log(value);
		this.setState(value);
	}
	handleSubmit(event) {
		alert(`Pressed submit button.`);
		this.requestReservation();
		console.log([this.state.date, this.state.num_guests]);
		event.preventDefault();
	}
	render() {
		return (
			<div>
			  <h1>Make a Reservation.</h1>
			  <p>Please select your desired reservation.</p>
			  <form onSubmit={this.handleSubmit}>
				<input onChange={this.handleChange}
					   type="datetime-local" name="date" />
				<input onChange={this.handleChange}
					   type="number" name="num_guests" min="1" max="20" />
				<input type="submit" value="check availability" />
			  </form>
			</div>
		);
	}
}

export default SelectRes;
