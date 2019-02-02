import React, {Component} from 'react';
import {BrowserRouter, Route, Redirect, Switch} from 'react-router-dom';

import Welcome from './welcome/Welcome';

class Content extends Component {
	constructor(props) {
		super(props);
	}
	render() {
		return (
			<div className="col-sm-10">
			  <main className="Content">
				<BrowserRouter>
				  <switch>
					<Route exact path='/' component={Welcome} />
					<Route exact path='/reservation' component={SelectRes} />
				  </switch>
				</BrowserRouter>
			  </main>
			</div>
		);
	}
}
export default Content;
